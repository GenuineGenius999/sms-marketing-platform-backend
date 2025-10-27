import secrets
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.compliance import (
    ContactOptIn, ComplianceLog, UnsubscribeToken, 
    ComplianceSettings, MessageCompliance
)
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.models.message import Message
from app.models.user import User
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class ComplianceService:
    def __init__(self, db: Session):
        self.db = db

    def create_opt_in(self, contact_id: int, user_id: int, opt_in_data: Dict[str, Any]):
        """Create an opt-in record for a contact"""
        try:
            opt_in = ContactOptIn(
                contact_id=contact_id,
                user_id=user_id,
                status=opt_in_data.get("status", "opted_in"),
                opt_in_method=opt_in_data.get("opt_in_method"),
                opt_in_source=opt_in_data.get("opt_in_source"),
                opt_in_timestamp=opt_in_data.get("opt_in_timestamp", datetime.utcnow()),
                ip_address=opt_in_data.get("ip_address"),
                user_agent=opt_in_data.get("user_agent"),
                consent_text=opt_in_data.get("consent_text")
            )

            self.db.add(opt_in)
            self.db.commit()
            self.db.refresh(opt_in)

            # Log compliance action
            self._log_compliance_action(
                user_id=user_id,
                contact_id=contact_id,
                action="opt_in",
                compliance_type="tcpa",
                details=opt_in_data
            )

            return {"success": True, "opt_in_id": opt_in.id}

        except Exception as e:
            logger.error(f"Error creating opt-in: {str(e)}")
            return {"success": False, "error": str(e)}

    def process_opt_out(self, contact_id: int, user_id: int, opt_out_data: Dict[str, Any]):
        """Process an opt-out request"""
        try:
            # Update or create opt-in record
            opt_in = self.db.query(ContactOptIn).filter(
                ContactOptIn.contact_id == contact_id,
                ContactOptIn.user_id == user_id
            ).first()

            if not opt_in:
                opt_in = ContactOptIn(
                    contact_id=contact_id,
                    user_id=user_id,
                    status="opted_out",
                    opt_out_timestamp=datetime.utcnow()
                )
                self.db.add(opt_in)
            else:
                opt_in.status = "opted_out"
                opt_in.opt_out_timestamp = datetime.utcnow()

            self.db.commit()

            # Log compliance action
            self._log_compliance_action(
                user_id=user_id,
                contact_id=contact_id,
                action="opt_out",
                compliance_type="tcpa",
                details=opt_out_data
            )

            return {"success": True, "message": "Contact opted out successfully"}

        except Exception as e:
            logger.error(f"Error processing opt-out: {str(e)}")
            return {"success": False, "error": str(e)}

    def generate_unsubscribe_token(self, contact_id: int, user_id: int) -> str:
        """Generate a secure unsubscribe token"""
        try:
            # Create token
            token = secrets.token_urlsafe(32)
            
            # Store token in database
            unsubscribe_token = UnsubscribeToken(
                contact_id=contact_id,
                user_id=user_id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(days=30)  # 30 days expiry
            )

            self.db.add(unsubscribe_token)
            self.db.commit()

            return token

        except Exception as e:
            logger.error(f"Error generating unsubscribe token: {str(e)}")
            return None

    def process_unsubscribe_token(self, token: str) -> Dict[str, Any]:
        """Process an unsubscribe token"""
        try:
            # Find token
            unsubscribe_token = self.db.query(UnsubscribeToken).filter(
                UnsubscribeToken.token == token,
                UnsubscribeToken.is_used == False,
                UnsubscribeToken.expires_at > datetime.utcnow()
            ).first()

            if not unsubscribe_token:
                return {"success": False, "error": "Invalid or expired token"}

            # Mark token as used
            unsubscribe_token.is_used = True
            unsubscribe_token.used_at = datetime.utcnow()

            # Process opt-out
            result = self.process_opt_out(
                contact_id=unsubscribe_token.contact_id,
                user_id=unsubscribe_token.user_id,
                opt_out_data={"method": "unsubscribe_link"}
            )

            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"Error processing unsubscribe token: {str(e)}")
            return {"success": False, "error": str(e)}

    def validate_message_compliance(self, message: str, user_id: int) -> Dict[str, Any]:
        """Validate message for compliance requirements"""
        try:
            compliance_issues = []
            warnings = []

            # TCPA Compliance checks
            if not self._has_opt_out_instruction(message):
                compliance_issues.append("Message must include opt-out instructions")

            if not self._has_sender_identification(message):
                compliance_issues.append("Message must identify the sender")

            # Check for prohibited content
            prohibited_patterns = [
                r'\b(urgent|emergency|immediate)\b',
                r'\b(act now|limited time|expires today)\b',
                r'\b(free money|win money|cash prize)\b'
            ]

            for pattern in prohibited_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    warnings.append(f"Message contains potentially problematic content: {pattern}")

            # Check message length
            if len(message) > 160:
                warnings.append("Message exceeds single SMS length (160 characters)")

            # Get user's compliance settings
            compliance_settings = self.db.query(ComplianceSettings).filter(
                ComplianceSettings.user_id == user_id,
                ComplianceSettings.compliance_type == "tcpa"
            ).first()

            if compliance_settings and compliance_settings.settings:
                settings = compliance_settings.settings
                
                # Check if opt-out instruction is required
                if settings.get("require_opt_out", True) and not self._has_opt_out_instruction(message):
                    compliance_issues.append("Opt-out instruction required by user settings")

            return {
                "success": len(compliance_issues) == 0,
                "compliance_issues": compliance_issues,
                "warnings": warnings,
                "is_compliant": len(compliance_issues) == 0
            }

        except Exception as e:
            logger.error(f"Error validating message compliance: {str(e)}")
            return {"success": False, "error": str(e)}

    def _has_opt_out_instruction(self, message: str) -> bool:
        """Check if message contains opt-out instruction"""
        opt_out_patterns = [
            r'opt.?out',
            r'stop',
            r'unsubscribe',
            r'text stop',
            r'reply stop',
            r'remove'
        ]

        for pattern in opt_out_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def _has_sender_identification(self, message: str) -> bool:
        """Check if message identifies the sender"""
        # This is a simple check - in practice, you might want more sophisticated logic
        sender_patterns = [
            r'from\s+\w+',
            r'-\s*\w+',
            r'\(\w+\)',
            r'company\s+name',
            r'business\s+name'
        ]

        for pattern in sender_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def _log_compliance_action(self, user_id: int, contact_id: int, action: str, 
                             compliance_type: str, details: Dict[str, Any]):
        """Log a compliance action"""
        try:
            log_entry = ComplianceLog(
                user_id=user_id,
                contact_id=contact_id,
                action=action,
                compliance_type=compliance_type,
                details=details,
                timestamp=datetime.utcnow()
            )

            self.db.add(log_entry)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error logging compliance action: {str(e)}")

    def get_contact_compliance_status(self, contact_id: int, user_id: int) -> Dict[str, Any]:
        """Get compliance status for a contact"""
        try:
            opt_in = self.db.query(ContactOptIn).filter(
                ContactOptIn.contact_id == contact_id,
                ContactOptIn.user_id == user_id
            ).first()

            if not opt_in:
                return {
                    "status": "unknown",
                    "can_send": False,
                    "opt_in_date": None,
                    "opt_out_date": None
                }

            return {
                "status": opt_in.status,
                "can_send": opt_in.status == "opted_in",
                "opt_in_date": opt_in.opt_in_timestamp,
                "opt_out_date": opt_in.opt_out_timestamp,
                "opt_in_method": opt_in.opt_in_method,
                "consent_text": opt_in.consent_text
            }

        except Exception as e:
            logger.error(f"Error getting contact compliance status: {str(e)}")
            return {"status": "error", "can_send": False}

    def create_compliance_settings(self, user_id: int, compliance_type: str, settings: Dict[str, Any]):
        """Create or update compliance settings for a user"""
        try:
            existing = self.db.query(ComplianceSettings).filter(
                ComplianceSettings.user_id == user_id,
                ComplianceSettings.compliance_type == compliance_type
            ).first()

            if existing:
                existing.settings = settings
                existing.updated_at = datetime.utcnow()
            else:
                compliance_settings = ComplianceSettings(
                    user_id=user_id,
                    compliance_type=compliance_type,
                    settings=settings
                )
                self.db.add(compliance_settings)

            self.db.commit()
            return {"success": True}

        except Exception as e:
            logger.error(f"Error creating compliance settings: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_compliance_report(self, user_id: int, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Generate a compliance report for a user"""
        try:
            query = self.db.query(ComplianceLog).filter(ComplianceLog.user_id == user_id)

            if start_date:
                query = query.filter(ComplianceLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ComplianceLog.timestamp <= end_date)

            logs = query.all()

            # Count actions by type
            action_counts = {}
            for log in logs:
                action = log.action
                action_counts[action] = action_counts.get(action, 0) + 1

            # Count by compliance type
            compliance_counts = {}
            for log in logs:
                compliance_type = log.compliance_type
                compliance_counts[compliance_type] = compliance_counts.get(compliance_type, 0) + 1

            return {
                "total_actions": len(logs),
                "action_counts": action_counts,
                "compliance_counts": compliance_counts,
                "period": {
                    "start": start_date,
                    "end": end_date
                }
            }

        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {"success": False, "error": str(e)}
