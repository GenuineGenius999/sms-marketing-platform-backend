import json
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.ab_testing import (
    ABTestCampaign, ABTestVariant, ABTestRecipient, ABTestResult,
    TestStatus, TestType
)
from app.models.contact import Contact
from app.models.user import User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ABTestingService:
    def __init__(self, db: Session):
        self.db = db

    async def create_ab_test(self, user_id: int, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B test campaign"""
        try:
            # Create the main test campaign
            campaign = ABTestCampaign(
                user_id=user_id,
                name=test_data["name"],
                description=test_data.get("description"),
                test_type=test_data["test_type"],
                traffic_split=test_data.get("traffic_split", 0.5),
                test_duration_days=test_data.get("test_duration_days", 7),
                minimum_sample_size=test_data.get("minimum_sample_size", 100),
                confidence_level=test_data.get("confidence_level", 0.95),
                status=TestStatus.DRAFT
            )
            
            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)
            
            # Create variants
            for variant_data in test_data["variants"]:
                variant = ABTestVariant(
                    campaign_id=campaign.id,
                    variant_name=variant_data["variant_name"],
                    variant_type=test_data["test_type"],
                    message_content=variant_data.get("message_content"),
                    sender_id=variant_data.get("sender_id"),
                    send_time=variant_data.get("send_time"),
                    subject_line=variant_data.get("subject_line")
                )
                self.db.add(variant)
            
            self.db.commit()
            
            return {"success": True, "campaign_id": campaign.id}
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {str(e)}")
            return {"success": False, "error": str(e)}

    async def start_ab_test(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """Start an A/B test campaign"""
        try:
            campaign = self.db.query(ABTestCampaign).filter(
                ABTestCampaign.id == campaign_id,
                ABTestCampaign.user_id == user_id
            ).first()
            
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign.status != TestStatus.DRAFT:
                return {"success": False, "error": "Campaign is not in draft status"}
            
            # Update campaign status
            campaign.status = TestStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            
            # Get target contacts
            contacts = self.db.query(Contact).filter(
                Contact.user_id == user_id
            ).all()
            
            if len(contacts) < campaign.minimum_sample_size:
                return {"success": False, "error": f"Not enough contacts. Need {campaign.minimum_sample_size}, have {len(contacts)}"}
            
            # Randomly assign contacts to variants
            import random
            random.shuffle(contacts)
            
            split_point = int(len(contacts) * campaign.traffic_split)
            variant_a_contacts = contacts[:split_point]
            variant_b_contacts = contacts[split_point:]
            
            # Get variants
            variants = self.db.query(ABTestVariant).filter(
                ABTestVariant.campaign_id == campaign_id
            ).all()
            
            variant_a = next((v for v in variants if v.variant_name == "A"), None)
            variant_b = next((v for v in variants if v.variant_name == "B"), None)
            
            if not variant_a or not variant_b:
                return {"success": False, "error": "Variants not found"}
            
            # Create recipients for variant A
            for contact in variant_a_contacts:
                recipient = ABTestRecipient(
                    campaign_id=campaign_id,
                    variant_id=variant_a.id,
                    contact_id=contact.id
                )
                self.db.add(recipient)
            
            # Create recipients for variant B
            for contact in variant_b_contacts:
                recipient = ABTestRecipient(
                    campaign_id=campaign_id,
                    variant_id=variant_b.id,
                    contact_id=contact.id
                )
                self.db.add(recipient)
            
            # Update variant recipient counts
            variant_a.recipients_count = len(variant_a_contacts)
            variant_b.recipients_count = len(variant_b_contacts)
            
            campaign.variant_a_recipients = len(variant_a_contacts)
            campaign.variant_b_recipients = len(variant_b_contacts)
            
            self.db.commit()
            
            return {"success": True, "message": "A/B test started successfully"}
            
        except Exception as e:
            logger.error(f"Error starting A/B test: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_ab_test_metrics(self, campaign_id: int, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update metrics for an A/B test"""
        try:
            campaign = self.db.query(ABTestCampaign).filter(
                ABTestCampaign.id == campaign_id
            ).first()
            
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            # Update campaign metrics
            for key, value in metrics_data.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)
            
            # Calculate conversion rates
            if campaign.variant_a_recipients > 0:
                campaign.variant_a_conversion_rate = campaign.variant_a_opened / campaign.variant_a_recipients
            
            if campaign.variant_b_recipients > 0:
                campaign.variant_b_conversion_rate = campaign.variant_b_opened / campaign.variant_b_recipients
            
            self.db.commit()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error updating A/B test metrics: {str(e)}")
            return {"success": False, "error": str(e)}

    async def analyze_ab_test(self, campaign_id: int) -> Dict[str, Any]:
        """Perform statistical analysis on A/B test results"""
        try:
            campaign = self.db.query(ABTestCampaign).filter(
                ABTestCampaign.id == campaign_id
            ).first()
            
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            # Get variant data
            variant_a_recipients = campaign.variant_a_recipients
            variant_b_recipients = campaign.variant_b_recipients
            variant_a_conversions = campaign.variant_a_opened
            variant_b_conversions = campaign.variant_b_opened
            
            if variant_a_recipients == 0 or variant_b_recipients == 0:
                return {"success": False, "error": "Insufficient data for analysis"}
            
            # Calculate conversion rates
            rate_a = variant_a_conversions / variant_a_recipients
            rate_b = variant_b_conversions / variant_b_recipients
            
            # Perform statistical significance test (Z-test for proportions)
            p1, p2 = rate_a, rate_b
            n1, n2 = variant_a_recipients, variant_b_recipients
            
            # Pooled proportion
            p_pooled = (variant_a_conversions + variant_b_conversions) / (n1 + n2)
            
            # Standard error
            se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
            
            # Z-score
            z_score = (p2 - p1) / se if se > 0 else 0
            
            # P-value (approximate)
            p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
            
            # Statistical significance
            is_significant = p_value < (1 - campaign.confidence_level)
            
            # Effect size (Cohen's h)
            effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))
            
            # Confidence interval
            diff = p2 - p1
            margin_error = 1.96 * se  # 95% confidence
            ci_lower = diff - margin_error
            ci_upper = diff + margin_error
            
            # Determine winner
            winner = None
            improvement_percentage = 0
            
            if is_significant:
                if rate_b > rate_a:
                    winner = "B"
                    improvement_percentage = ((rate_b - rate_a) / rate_a) * 100
                elif rate_a > rate_b:
                    winner = "A"
                    improvement_percentage = ((rate_a - rate_b) / rate_b) * 100
            else:
                winner = "inconclusive"
            
            # Create result record
            result = ABTestResult(
                campaign_id=campaign_id,
                variant_a_metrics=json.dumps({
                    "recipients": variant_a_recipients,
                    "conversions": variant_a_conversions,
                    "conversion_rate": rate_a
                }),
                variant_b_metrics=json.dumps({
                    "recipients": variant_b_recipients,
                    "conversions": variant_b_conversions,
                    "conversion_rate": rate_b
                }),
                statistical_significance=p_value,
                confidence_interval=json.dumps({
                    "lower": ci_lower,
                    "upper": ci_upper
                }),
                p_value=p_value,
                effect_size=effect_size,
                winner_variant=winner,
                improvement_percentage=improvement_percentage,
                sample_size=n1 + n2,
                test_duration_hours=self._calculate_test_duration(campaign)
            )
            
            self.db.add(result)
            
            # Update campaign with results
            campaign.statistical_significance = p_value
            campaign.winner_variant = winner
            
            self.db.commit()
            
            return {
                "success": True,
                "analysis": {
                    "variant_a_rate": rate_a,
                    "variant_b_rate": rate_b,
                    "statistical_significance": p_value,
                    "is_significant": is_significant,
                    "winner": winner,
                    "improvement_percentage": improvement_percentage,
                    "effect_size": effect_size,
                    "confidence_interval": {"lower": ci_lower, "upper": ci_upper}
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing A/B test: {str(e)}")
            return {"success": False, "error": str(e)}

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF using error function"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _calculate_test_duration(self, campaign: ABTestCampaign) -> float:
        """Calculate test duration in hours"""
        if campaign.started_at and campaign.completed_at:
            delta = campaign.completed_at - campaign.started_at
            return delta.total_seconds() / 3600
        elif campaign.started_at:
            delta = datetime.utcnow() - campaign.started_at
            return delta.total_seconds() / 3600
        return 0.0

    async def get_ab_test_stats(self, user_id: int) -> Dict[str, Any]:
        """Get A/B testing statistics for a user"""
        try:
            campaigns = self.db.query(ABTestCampaign).filter(
                ABTestCampaign.user_id == user_id
            ).all()
            
            total_tests = len(campaigns)
            running_tests = len([c for c in campaigns if c.status == TestStatus.RUNNING])
            completed_tests = len([c for c in campaigns if c.status == TestStatus.COMPLETED])
            
            # Calculate average improvement
            successful_tests = [c for c in campaigns if c.winner_variant and c.winner_variant != "inconclusive"]
            avg_improvement = sum([c.variant_a_conversion_rate + c.variant_b_conversion_rate for c in successful_tests]) / len(successful_tests) if successful_tests else 0
            
            # Most effective test type
            test_types = [c.test_type.value for c in successful_tests]
            most_effective = max(set(test_types), key=test_types.count) if test_types else "message_content"
            
            return {
                "total_tests": total_tests,
                "running_tests": running_tests,
                "completed_tests": completed_tests,
                "successful_tests": len(successful_tests),
                "average_improvement": avg_improvement,
                "most_effective_test_type": most_effective
            }
            
        except Exception as e:
            logger.error(f"Error getting A/B test stats: {str(e)}")
            return {"success": False, "error": str(e)}
