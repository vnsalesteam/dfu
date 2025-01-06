import streamlit as st
import anthropic
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

class EnhancedDemoAnalyzer:
    def __init__(self):
        """Initialize the demo analyzer with API key from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
            
        self.client = anthropic.Client(api_key=api_key)
        self.system_prompt = """You are an expert sales analyst specializing in healthcare technology demos. 
        Extract detailed insights with a focus on pain points, buying signals, and actionable next steps."""

    def analyze_transcript(self, transcript: str) -> Optional[Dict]:
        """
        Enhanced analysis that includes pain points, buying signals, and deeper technical insights.
        Returns a structured dictionary of findings.
        """
        try:
            # First, clean and prepare the transcript
            cleaned_transcript = transcript.strip().replace('\n', ' ').replace('\r', '')
            
            # Add a JSON validation step
            def validate_json_response(text: str) -> Dict:
                try:
                    # Remove any potential markdown markers
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0]
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0]
                    return json.loads(text.strip())
                except json.JSONDecodeError as e:
                    st.error(f"JSON parsing error: {str(e)}")
                    st.error("Raw response: " + text[:500] + "...")
                    raise
            message = self.client.messages.create(
                system=self.system_prompt,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this sales demo transcript and extract comprehensive insights. 
                    
Return your response as a valid JSON object (not a string) with these exact keys. Ensure all values are properly formatted as arrays or objects as specified:

technical_requirements: [
    List specific technical details including:
    - EHR systems and versions
    - Integration requirements
    - Security/compliance needs
    - Infrastructure specifications
]

pain_points: {{
    "operational": [List of operational challenges mentioned],
    "technical": [List of technical challenges],
    "financial": [List of cost/budget related issues],
    "clinical": [List of clinical workflow challenges],
    "priority_level": Map of each pain point to High/Medium/Low based on urgency in discussion
}}

buying_signals: {{
    "budget_indicators": [Phrases indicating budget availability/constraints],
    "timeline_urgency": [Mentions of urgent needs or deadlines],
    "decision_process": [Information about approval process],
    "competitor_mentions": [Any competing solutions discussed],
    "positive_signals": [Encouraging comments/reactions],
    "concerns": [Expressed doubts or worries]
}}

stakeholders: {{
    "decision_makers": [List with roles and influence level],
    "technical_reviewers": [Technical stakeholders],
    "end_users": [Who will use the system],
    "other_stakeholders": [Additional involved parties]
}}

timeline_info: {{
    "start_date": Exact date mentioned,
    "implementation_phases": [List of phases with dates],
    "dependencies": [Prerequisites or blockers],
    "key_milestones": [Important timeline events]
}}

pricing_discussion: {{
    "model_discussed": Pricing model details,
    "budget_constraints": Any mentioned limits,
    "competitor_pricing": Any mentioned competitive prices,
    "volume_considerations": Volume-related details
}}

next_steps: [
    List each action item with:
    {{
        "action": Specific task,
        "owner": Responsible party,
        "deadline": Due date,
        "priority": High/Medium/Low
    }}
]

TRANSCRIPT:
{transcript}
"""
                }],
                model="claude-3-haiku-20240307"
            )
            response_text = message.content[0].text
            return validate_json_response(response_text)
        except Exception as e:
            st.error(f"Error analyzing transcript: {str(e)}")
            return None

    def generate_email_template(self, insights: Dict, contact_name: str, template_type: str = "standard") -> str:
        """
        Generates a customized follow-up email based on the analysis and template type.
        Different templates for different scenarios (technical, executive, etc.)
        """
        try:
            template_prompts = {
                "technical": "Focus on technical details and integration pathway",
                "executive": "Emphasize ROI and strategic value",
                "clinical": "Focus on clinical workflow improvements and patient care",
                "standard": "Balanced overview of all aspects"
            }

            prompt = template_prompts.get(template_type, template_prompts["standard"])

            message = self.client.messages.create(
                system="You are a professional sales representative crafting a strategic follow-up email.",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Write a strategic follow-up email to {contact_name}. 

Requirements:
1. Address key pain points identified and how we solve them
2. Reference specific technical requirements discussed
3. Acknowledge timeline needs
4. Include clear next steps with ownership
5. Maintain urgency while being professional

Style Guide:
- Clear and concise
- Professional but conversational
- Action-oriented
- Value-focused

Template Focus: {prompt}

INSIGHTS:
{json.dumps(insights, indent=2)}"""
                }],
                model="claude-3-haiku-20240307"
            )
            return message.content[0].text
        except Exception as e:
            st.error(f"Error generating email: {str(e)}")
            return ""

def main():
    st.set_page_config(layout="wide", page_title="Enhanced Demo Analysis Tool")
    st.title("🎯 Enhanced Demo Analysis Tool")

    if 'insights' not in st.session_state:
        st.session_state.insights = None
    if 'email_draft' not in st.session_state:
        st.session_state.email_draft = None

    with st.sidebar:
        st.header("Demo Information")
        contact_name = st.text_input("Primary Contact Name")
        contact_role = st.text_input("Contact Role")
        demo_date = st.date_input("Demo Date")
        template_type = st.selectbox(
            "Email Template Type",
            ["standard", "technical", "executive", "clinical"]
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Demo Transcript")
        transcript = st.text_area("Paste transcript here:", height=300)
        
        if st.button("Analyze Demo"):
            if not transcript:
                st.error("Please paste a demo transcript")
                return
                
            with st.spinner("Analyzing transcript..."):
                analyzer = EnhancedDemoAnalyzer()
                st.session_state.insights = analyzer.analyze_transcript(transcript)
                if contact_name and st.session_state.insights:
                    st.session_state.email_draft = analyzer.generate_email_template(
                        st.session_state.insights,
                        contact_name,
                        template_type
                    )

    with col2:
        if st.session_state.insights:
            insights = st.session_state.insights
            
            st.subheader("Key Insights")
            
            with st.expander("Pain Points", expanded=True):
                for category, points in insights['pain_points'].items():
                    if category != 'priority_level':
                        st.markdown(f"**{category.title()}**")
                        for point in points:
                            priority = insights['pain_points']['priority_level'].get(point, 'Medium')
                            emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            st.markdown(f"{emoji} {point}")

            with st.expander("Buying Signals", expanded=True):
                for signal_type, signals in insights['buying_signals'].items():
                    st.markdown(f"**{signal_type.replace('_', ' ').title()}**")
                    for signal in signals:
                        st.markdown(f"• {signal}")

            with st.expander("Technical Requirements"):
                for req in insights['technical_requirements']:
                    st.markdown(f"• {req}")
                    
            with st.expander("Stakeholders"):
                for role, people in insights['stakeholders'].items():
                    st.markdown(f"**{role.replace('_', ' ').title()}**")
                    for person in people:
                        st.markdown(f"• {person}")

            with st.expander("Timeline"):
                timeline = insights['timeline_info']
                st.markdown(f"**Start Date:** {timeline['start_date']}")
                st.markdown("**Implementation Phases:**")
                for phase in timeline['implementation_phases']:
                    st.markdown(f"• {phase}")
                if timeline.get('dependencies'):
                    st.markdown("**Dependencies:**")
                    for dep in timeline['dependencies']:
                        st.markdown(f"• {dep}")
                        
            with st.expander("Pricing Discussion"):
                for key, value in insights['pricing_discussion'].items():
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                    
            st.subheader("Action Items")
            for item in insights['next_steps']:
                priority_emoji = "🔴" if item['priority'] == "High" else "🟡" if item['priority'] == "Medium" else "🟢"
                st.checkbox(
                    f"{priority_emoji} {item['action']} (Owner: {item['owner']}, Due: {item['deadline']})",
                    key=f"action_{item['action'][:20]}"
                )

    if st.session_state.email_draft:
        st.markdown("---")
        st.subheader("Follow-up Email Draft")
        email_text = st.text_area("Email Content", st.session_state.email_draft, height=200)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Copy to Clipboard"):
                st.write("Email copied!")
        with col2:
            st.download_button(
                "Download Analysis",
                data=json.dumps(st.session_state.insights, indent=2),
                file_name=f"demo_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()