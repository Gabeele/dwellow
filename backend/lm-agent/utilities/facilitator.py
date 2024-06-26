from agents.intent_classifier import IntentClassifier
import agents.response_generator as response_generator
from agents.maintenance_request_agent import MaintenanceRequestAgent
from utilities.db import create_ticket
from agents.humanize_agent import Humanize
import logging

class Facilitator:
    def __init__(self, session):
        self.session = session
        self.maintenance_agent = MaintenanceRequestAgent()
        self.humanizer = Humanize()
        self.intent_classifier = IntentClassifier()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            newSession = True
            done = False
            while not done:
                if newSession:
                    self.send_message("Hello! How can I help you today?")
                    newSession = False
                else:
                    self.send_message("Is there anything else I can help you with?")

                user_input = self.receive_message()
                if user_input is None:
                    done = True
                    continue

                intent = self.get_intent(user_input)
                response, done = self.process_intent(intent, user_input)
                if response:
                    self.send_message(response)
        except Exception as e:
            self.logger.error(f"An error occurred during the session: {e}")
            self.send_message("An error occurred. Please try again later.")
        finally:
            self.session.disconnect()

    def maintenance_request_process(self):
        done = False
        while not done:
            try:
                key, next_question = self.maintenance_agent.get_next_question()
                if next_question:
                    self.send_message(next_question)
                    user_response = self.receive_message()
                    if user_response is None:
                        done = True
                        continue
                    
                    if key == "emergency" and user_response.strip().lower() in ["yes", "y"]:
                        self.send_message("Call 911 now.")
                        done = True
                    else:
                        self.maintenance_agent.handle_response(key, user_response)
                else:
                    ticket_data = self.maintenance_agent.finalize_ticket()
                    self.create_ticket_in_db(ticket_data)
                    self.send_message("Sending your maintenance request now. Is there anything else I can help you with?")
                    done = True
            except Exception as e:
                self.logger.error(f"An error occurred during the maintenance request process: {e}")
                self.send_message("An error occurred while processing your request. Please try again.")
                done = True

    def create_ticket_in_db(self, ticket_data):
        try:
            unit_id = self.session.user_id  # For now, the unit_id is the same as the user_id
            user_id = self.session.user_id
            description = ticket_data.get("issue_detail")
            length = ticket_data.get("duration")
            severity = int(ticket_data.get("severity", 0))
            urgency = int(ticket_data.get("urgency", 0))
            priority = self.determine_priority(severity, urgency)
            issue_area = ticket_data.get("issue_area", "Maintenance")
            photo_url = "http://example.com/photo.jpg"
            special_instructions = ticket_data.get("additional_details")

            create_ticket(
                unit_id,
                user_id,
                description,
                length,
                priority,
                issue_area,
                photo_url,
                special_instructions
            )
        except Exception as e:
            self.logger.error(f"An error occurred while creating the ticket: {e}")
            self.send_message("An error occurred while creating the ticket. Please try again.")

    def determine_priority(self, severity, urgency):
        if severity >= 8 or urgency >= 8:
            return "High"
        elif severity >= 5 or urgency >= 5:
            return "Medium"
        else:
            return "Low"

    def process_intent(self, intent, user_input):
        response = None
        done = False
        try:
            if intent == "unknown":
                response = response_generator.generate_response("unknown")
            elif intent == "greet":
                response = response_generator.generate_response("greet")
            elif intent == "farewell":
                response = response_generator.generate_response("farewell")
                done = True
            elif intent == "maintenance request":
                self.maintenance_request_process()
            else:
                response = response_generator.generate_response(intent)
        except Exception as e:
            self.logger.error(f"An error occurred while processing intent: {e}")
            response = "An error occurred while processing your request. Please try again."
        return response, done

    def send_message(self, message):
        humanized_message = self.humanizer.generate_response(message)
        try:
            self.session.socket.send(humanized_message)
        except Exception as e:
            self.logger.error(f"An error occurred while sending data: {e}")
            self.session.disconnect()

    def receive_message(self):
        try:
            return self.session.socket.receive()
        except Exception as e:
            self.logger.error(f"An error occurred while receiving data: {e}")
            self.session.disconnect()
            return None

    def get_intent(self, data):
        return self.intent_classifier.classify_intent(data)
