"""
Smart Notification Classifier
Classifies alerts by priority based on EV and confidence
"""
from enum import Enum

class Priority(Enum):
    URGENT = "🔥"      # EV > 1.5, Confidence > 80%
    IMPORTANT = "📢"   # EV > 1.2, Confidence > 60%
    INFO = "ℹ️"        # Others

class NotificationClassifier:
    def __init__(self):
        self.urgent_ev = 1.5
        self.urgent_conf = 0.80
        self.important_ev = 1.2
        self.important_conf = 0.60
    
    def classify(self, expected_value, confidence):
        """
        Classify notification priority
        
        Args:
            expected_value: Expected value (payout / bet)
            confidence: Prediction confidence (0-1)
        
        Returns:
            Priority enum
        """
        if expected_value >= self.urgent_ev and confidence >= self.urgent_conf:
            return Priority.URGENT
        elif expected_value >= self.important_ev and confidence >= self.important_conf:
            return Priority.IMPORTANT
        else:
            return Priority.INFO
    
    def format_message(self, priority, race_info, prediction_info):
        """
        Format notification message with priority
        
        Args:
            priority: Priority enum
            race_info: Dict with race details
            prediction_info: Dict with prediction details
        
        Returns:
            Formatted message string
        """
        icon = priority.value
        level = priority.name
        
        msg = f"{icon} **{level}** Alert\n"
        msg += f"会場: {race_info.get('jyo_name', 'N/A')} {race_info.get('race_no', 'N/A')}R\n"
        msg += f"買い目: {prediction_info.get('combination', 'N/A')}\n"
        msg += f"期待値: {prediction_info.get('ev', 0):.2f}倍\n"
        msg += f"信頼度: {prediction_info.get('confidence', 0)*100:.1f}%\n"
        
        # Add urgency note for URGENT
        if priority == Priority.URGENT:
            msg += "\n⚠️ 高期待値！今すぐチェック推奨"
        
        return msg

# Global instance
classifier = NotificationClassifier()

if __name__ == "__main__":
    # Test cases
    print("Test 1: URGENT")
    p1 = classifier.classify(1.6, 0.85)
    print(f"Priority: {p1.name} {p1.value}")
    
    print("\nTest 2: IMPORTANT")
    p2 = classifier.classify(1.3, 0.70)
    print(f"Priority: {p2.name} {p2.value}")
    
    print("\nTest 3: INFO")
    p3 = classifier.classify(1.1, 0.55)
    print(f"Priority: {p3.name} {p3.value}")
    
    # Format message
    print("\n" + "=" * 40)
    msg = classifier.format_message(
        p1,
        {"jyo_name": "桐生", "race_no": 12},
        {"combination": "1-2-3", "ev": 1.6, "confidence": 0.85}
    )
    print(msg)
