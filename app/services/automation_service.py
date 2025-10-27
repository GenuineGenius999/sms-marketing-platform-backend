import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.automation import (
    AutomationWorkflow, AutomationExecution, KeywordTrigger, 
    DripCampaign, DripCampaignStep, DripCampaignContact
)
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.models.message import Message, MessageStatus
from app.models.template import SmsTemplate
from app.services.sms_service import sms_service
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self, db: Session):
        self.db = db

    async def process_keyword_trigger(self, phone: str, message: str, user_id: int):
        """Process incoming SMS for keyword triggers"""
        try:
            # Find contact by phone
            contact = self.db.query(Contact).filter(
                Contact.phone == phone,
                Contact.user_id == user_id
            ).first()

            if not contact:
                return {"success": False, "error": "Contact not found"}

            # Find matching keyword triggers
            triggers = self.db.query(KeywordTrigger).filter(
                KeywordTrigger.user_id == user_id,
                KeywordTrigger.is_active == True
            ).all()

            for trigger in triggers:
                keyword = trigger.keyword.lower() if not trigger.is_case_sensitive else trigger.keyword
                message_lower = message.lower() if not trigger.is_case_sensitive else message

                if keyword in message_lower:
                    # Send response message
                    result = await sms_service.send_sms(
                        phone=phone,
                        message=trigger.response_message,
                        sender_id=None,
                        campaign_id=None
                    )

                    # Log the interaction
                    if result.get("success"):
                        logger.info(f"Keyword trigger '{trigger.keyword}' activated for {phone}")
                        return {"success": True, "response": trigger.response_message}
                    else:
                        logger.error(f"Failed to send keyword response: {result.get('error')}")
                        return {"success": False, "error": "Failed to send response"}

            return {"success": False, "error": "No matching keyword found"}

        except Exception as e:
            logger.error(f"Error processing keyword trigger: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_automation_workflow(self, workflow_data: Dict[str, Any], user_id: int):
        """Create a new automation workflow"""
        try:
            workflow = AutomationWorkflow(
                user_id=user_id,
                name=workflow_data["name"],
                description=workflow_data.get("description"),
                trigger_type=workflow_data["trigger_type"],
                trigger_config=workflow_data.get("trigger_config", {}),
                action_type=workflow_data["action_type"],
                action_config=workflow_data.get("action_config", {}),
                status=workflow_data.get("status", "active")
            )

            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)

            return {"success": True, "workflow_id": workflow.id}

        except Exception as e:
            logger.error(f"Error creating automation workflow: {str(e)}")
            return {"success": False, "error": str(e)}

    async def execute_workflow(self, workflow_id: int, contact_id: int, trigger_data: Dict[str, Any] = None):
        """Execute an automation workflow"""
        try:
            workflow = self.db.query(AutomationWorkflow).filter(
                AutomationWorkflow.id == workflow_id,
                AutomationWorkflow.is_active == True
            ).first()

            if not workflow:
                return {"success": False, "error": "Workflow not found"}

            contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return {"success": False, "error": "Contact not found"}

            # Create execution record
            execution = AutomationExecution(
                workflow_id=workflow_id,
                contact_id=contact_id,
                trigger_data=trigger_data or {},
                status="pending"
            )
            self.db.add(execution)
            self.db.commit()

            # Execute the action based on action_type
            action_result = await self._execute_action(workflow, contact, trigger_data)

            # Update execution record
            execution.action_result = action_result
            execution.status = "completed" if action_result.get("success") else "failed"
            execution.error_message = action_result.get("error")
            self.db.commit()

            return action_result

        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_action(self, workflow: AutomationWorkflow, contact: Contact, trigger_data: Dict[str, Any]):
        """Execute the specific action for a workflow"""
        try:
            action_type = workflow.action_type
            action_config = workflow.action_config or {}

            if action_type == "send_sms":
                message = action_config.get("message", "")
                # Replace placeholders in message
                message = message.replace("{name}", contact.name or "")
                message = message.replace("{phone}", contact.phone or "")
                message = message.replace("{email}", contact.email or "")

                result = await sms_service.send_sms(
                    phone=contact.phone,
                    message=message,
                    sender_id=action_config.get("sender_id"),
                    campaign_id=None
                )
                return result

            elif action_type == "add_to_group":
                group_id = action_config.get("group_id")
                if group_id:
                    contact.group_id = group_id
                    self.db.commit()
                return {"success": True, "message": "Contact added to group"}

            elif action_type == "remove_from_group":
                contact.group_id = None
                self.db.commit()
                return {"success": True, "message": "Contact removed from group"}

            elif action_type == "update_contact":
                # Update contact fields based on action_config
                for field, value in action_config.get("fields", {}).items():
                    if hasattr(contact, field):
                        setattr(contact, field, value)
                self.db.commit()
                return {"success": True, "message": "Contact updated"}

            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}

        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_drip_campaign(self, campaign_data: Dict[str, Any], user_id: int):
        """Create a drip campaign"""
        try:
            drip_campaign = DripCampaign(
                user_id=user_id,
                name=campaign_data["name"],
                description=campaign_data.get("description"),
                is_active=campaign_data.get("is_active", True)
            )

            self.db.add(drip_campaign)
            self.db.commit()
            self.db.refresh(drip_campaign)

            # Add steps if provided
            if "steps" in campaign_data:
                for step_data in campaign_data["steps"]:
                    step = DripCampaignStep(
                        campaign_id=drip_campaign.id,
                        step_order=step_data["step_order"],
                        delay_days=step_data.get("delay_days", 0),
                        delay_hours=step_data.get("delay_hours", 0),
                        message_template_id=step_data.get("message_template_id"),
                        message_content=step_data.get("message_content"),
                        is_active=step_data.get("is_active", True)
                    )
                    self.db.add(step)

            self.db.commit()
            return {"success": True, "campaign_id": drip_campaign.id}

        except Exception as e:
            logger.error(f"Error creating drip campaign: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_contact_to_drip_campaign(self, campaign_id: int, contact_id: int):
        """Add a contact to a drip campaign"""
        try:
            # Check if contact is already in campaign
            existing = self.db.query(DripCampaignContact).filter(
                DripCampaignContact.campaign_id == campaign_id,
                DripCampaignContact.contact_id == contact_id,
                DripCampaignContact.is_active == True
            ).first()

            if existing:
                return {"success": False, "error": "Contact already in campaign"}

            # Add contact to campaign
            campaign_contact = DripCampaignContact(
                campaign_id=campaign_id,
                contact_id=contact_id,
                current_step=0,
                is_active=True
            )

            self.db.add(campaign_contact)
            self.db.commit()

            # Start the drip campaign
            await self._process_drip_campaign_step(campaign_id, contact_id, 0)

            return {"success": True, "message": "Contact added to drip campaign"}

        except Exception as e:
            logger.error(f"Error adding contact to drip campaign: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _process_drip_campaign_step(self, campaign_id: int, contact_id: int, step_number: int):
        """Process a specific step in a drip campaign"""
        try:
            # Get the step
            step = self.db.query(DripCampaignStep).filter(
                DripCampaignStep.campaign_id == campaign_id,
                DripCampaignStep.step_order == step_number,
                DripCampaignStep.is_active == True
            ).first()

            if not step:
                return {"success": False, "error": "Step not found"}

            # Get contact
            contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return {"success": False, "error": "Contact not found"}

            # Prepare message
            message = step.message_content or ""
            if step.message_template_id:
                # Get template and merge with contact data
                template = self.db.query(SmsTemplate).filter(
                    SmsTemplate.id == step.message_template_id
                ).first()
                if template:
                    message = template.content

            # Replace placeholders
            message = message.replace("{name}", contact.name or "")
            message = message.replace("{phone}", contact.phone or "")
            message = message.replace("{email}", contact.email or "")

            # Send message
            result = await sms_service.send_sms(
                phone=contact.phone,
                message=message,
                sender_id=None,
                campaign_id=None
            )

            if result.get("success"):
                # Update campaign contact
                campaign_contact = self.db.query(DripCampaignContact).filter(
                    DripCampaignContact.campaign_id == campaign_id,
                    DripCampaignContact.contact_id == contact_id
                ).first()

                if campaign_contact:
                    campaign_contact.current_step = step_number + 1
                    self.db.commit()

                # Schedule next step if exists
                next_step = self.db.query(DripCampaignStep).filter(
                    DripCampaignStep.campaign_id == campaign_id,
                    DripCampaignStep.step_order == step_number + 1,
                    DripCampaignStep.is_active == True
                ).first()

                if next_step:
                    # Calculate delay
                    delay_seconds = (step.delay_days * 24 * 3600) + (step.delay_hours * 3600)
                    if delay_seconds > 0:
                        # In a real implementation, you'd use a task queue like Celery
                        # For now, we'll just log it
                        logger.info(f"Next step scheduled for {delay_seconds} seconds")

            return result

        except Exception as e:
            logger.error(f"Error processing drip campaign step: {str(e)}")
            return {"success": False, "error": str(e)}

    async def process_incoming_sms(self, phone: str, message: str, user_id: int):
        """Process incoming SMS for all automation triggers"""
        try:
            # Process keyword triggers
            keyword_result = await self.process_keyword_trigger(phone, message, user_id)
            
            # Process other automation workflows
            workflows = self.db.query(AutomationWorkflow).filter(
                AutomationWorkflow.user_id == user_id,
                AutomationWorkflow.trigger_type == "contact_action",
                AutomationWorkflow.is_active == True
            ).all()

            for workflow in workflows:
                # Find contact
                contact = self.db.query(Contact).filter(
                    Contact.phone == phone,
                    Contact.user_id == user_id
                ).first()

                if contact:
                    await self.execute_workflow(workflow.id, contact.id, {
                        "phone": phone,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            return keyword_result

        except Exception as e:
            logger.error(f"Error processing incoming SMS: {str(e)}")
            return {"success": False, "error": str(e)}
