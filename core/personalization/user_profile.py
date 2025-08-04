# core/personalization/user_profile.py
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

@dataclass
class UserPreference:
    preferred_language: str
    preferred_llm: str
    code_style: str  # "concise", "verbose", "documented"
    complexity_tolerance: float  # 0-1 scale
    response_length: str  # "short", "medium", "long"
    auto_completion: bool
    show_explanations: bool
    theme: str  # "light", "dark", "auto"

@dataclass
class UserBehavior:
    query_patterns: Dict[str, int]  # query_type -> count
    completion_acceptance_rate: float
    feedback_history: List[Dict[str, Any]]
    learning_progress: Dict[str, float]  # topic -> mastery level
    session_frequency: Dict[str, int]  # day_of_week -> count
    preferred_time_slots: List[str]  # ["morning", "afternoon", "evening", "night"]

@dataclass
class UserProfile:
    user_id: str
    preferences: UserPreference
    behavior: UserBehavior
    created_at: datetime
    last_updated: datetime
    skill_level: Dict[str, float]  # language -> skill level (0-1)

class UserProfileManager:
    def __init__(self, storage_path: str = "data/user_profiles"):
        self.storage_path = storage_path
        self.profiles: Dict[str, UserProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load user profiles from storage"""
        import os
        if os.path.exists(self.storage_path):
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    user_id = filename[:-5]  # Remove .json extension
                    with open(os.path.join(self.storage_path, filename), 'r') as f:
                        profile_data = json.load(f)
                        self.profiles[user_id] = self._deserialize_profile(profile_data)
    
    def _deserialize_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """Deserialize profile data from JSON"""
        return UserProfile(
            user_id=profile_data["user_id"],
            preferences=UserPreference(**profile_data["preferences"]),
            behavior=UserBehavior(**profile_data["behavior"]),
            created_at=datetime.fromisoformat(profile_data["created_at"]),
            last_updated=datetime.fromisoformat(profile_data["last_updated"]),
            skill_level=profile_data["skill_level"]
        )
    
    def get_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.profiles:
            self.profiles[user_id] = self._create_default_profile(user_id)
        
        return self.profiles[user_id]
    
    def _create_default_profile(self, user_id: str) -> UserProfile:
        """Create default user profile"""
        return UserProfile(
            user_id=user_id,
            preferences=UserPreference(
                preferred_language="python",
                preferred_llm="gpt-4",
                code_style="concise",
                complexity_tolerance=0.5,
                response_length="medium",
                auto_completion=True,
                show_explanations=True,
                theme="auto"
            ),
            behavior=UserBehavior(
                query_patterns={},
                completion_acceptance_rate=0.5,
                feedback_history=[],
                learning_progress={},
                session_frequency={},
                preferred_time_slots=[]
            ),
            created_at=datetime.now(),
            last_updated=datetime.now(),
            skill_level={"python": 0.5, "javascript": 0.3, "java": 0.2}
        )
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        profile = self.get_profile(user_id)
        
        # Update preferences
        if "preferences" in updates:
            for key, value in updates["preferences"].items():
                if hasattr(profile.preferences, key):
                    setattr(profile.preferences, key, value)
        
        # Update behavior
        if "behavior" in updates:
            for key, value in updates["behavior"].items():
                if hasattr(profile.behavior, key):
                    setattr(profile.behavior, key, value)
        
        # Update skill level
        if "skill_level" in updates:
            profile.skill_level.update(updates["skill_level"])
        
        profile.last_updated = datetime.now()
        self._save_profile(profile)
        
        return profile
    
    def record_interaction(self, user_id: str, interaction_data: Dict[str, Any]):
        """Record user interaction for learning"""
        profile = self.get_profile(user_id)
        
        # Update query patterns
        query_type = interaction_data.get("query_type", "general")
        profile.behavior.query_patterns[query_type] = profile.behavior.query_patterns.get(query_type, 0) + 1
        
        # Update completion acceptance
        if "completion_accepted" in interaction_data:
            if profile.behavior.completion_acceptance_rate is None:
                profile.behavior.completion_acceptance_rate = 0.0
            
            # Update acceptance rate with exponential moving average
            alpha = 0.1  # Learning rate
            if interaction_data["completion_accepted"]:
                profile.behavior.completion_acceptance_rate = (
                    alpha * 1.0 + (1 - alpha) * profile.behavior.completion_acceptance_rate
                )
            else:
                profile.behavior.completion_acceptance_rate = (
                    alpha * 0.0 + (1 - alpha) * profile.behavior.completion_acceptance_rate
                )
        
        # Update feedback history
        if "feedback" in interaction_data:
            profile.behavior.feedback_history.append({
                "timestamp": datetime.now().isoformat(),
                "feedback": interaction_data["feedback"],
                "query": interaction_data.get("query", ""),
                "response": interaction_data.get("response", "")
            })
            
            # Keep only last 100 feedback entries
            if len(profile.behavior.feedback_history) > 100:
                profile.behavior.feedback_history = profile.behavior.feedback_history[-100:]
        
        # Update session frequency
        if "session_time" in interaction_data:
            session_time = datetime.fromisoformat(interaction_data["session_time"])
            day_of_week = session_time.strftime("%A").lower()
            profile.behavior.session_frequency[day_of_week] = profile.behavior.session_frequency.get(day_of_week, 0) + 1
        
        # Update preferred time slots
        if "session_time" in interaction_data:
            hour = session_time.hour
            if 6 <= hour < 12:
                time_slot = "morning"
            elif 12 <= hour < 18:
                time_slot = "afternoon"
            elif 18 <= hour < 24:
                time_slot = "evening"
            else:
                time_slot = "night"
            
            if time_slot not in profile.behavior.preferred_time_slots:
                profile.behavior.preferred_time_slots.append(time_slot)
        
        # Update learning progress
        if "language" in interaction_data and "success" in interaction_data:
            language = interaction_data["language"]
            success = interaction_data["success"]
            
            if language not in profile.behavior.learning_progress:
                profile.behavior.learning_progress[language] = 0.5
            
            # Update learning progress
            alpha = 0.05  # Small learning rate for skill level
            if success:
                profile.behavior.learning_progress[language] = min(1.0, 
                    profile.behavior.learning_progress[language] + alpha)
            else:
                profile.behavior.learning_progress[language] = max(0.0, 
                    profile.behavior.learning_progress[language] - alpha * 0.5)
        
        # Update skill level based on learning progress
        for language, progress in profile.behavior.learning_progress.items():
            profile.skill_level[language] = progress
        
        profile.last_updated = datetime.now()
        self._save_profile(profile)
    
    def _save_profile(self, profile: UserProfile):
        """Save profile to storage"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
        
        profile_data = {
            "user_id": profile.user_id,
            "preferences": asdict(profile.preferences),
            "behavior": asdict(profile.behavior),
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
            "skill_level": profile.skill_level
        }
        
        with open(os.path.join(self.storage_path, f"{profile.user_id}.json"), 'w') as f:
            json.dump(profile_data, f, indent=2)
    
    def get_personalized_response_config(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized response configuration based on user profile"""
        profile = self.get_profile(user_id)
        
        config = {
            "language": profile.preferences.preferred_language,
            "llm": profile.preferences.preferred_llm,
            "style": profile.preferences.code_style,
            "length": profile.preferences.response_length,
            "show_explanations": profile.preferences.show_explanations,
            "complexity_level": profile.preferences.complexity_tolerance
        }
        
        # Adjust based on context
        if "language" in context:
            config["language"] = context["language"]
        
        # Adjust complexity based on user skill level
        if "language" in context and context["language"] in profile.skill_level:
            skill_level = profile.skill_level[context["language"]]
            if skill_level > 0.8:
                config["complexity_level"] = min(1.0, config["complexity_level"] + 0.2)
            elif skill_level < 0.3:
                config["complexity_level"] = max(0.0, config["complexity_level"] - 0.2)
        
        return config
    
    def get_learning_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get personalized learning recommendations"""
        profile = self.get_profile(user_id)
        
        recommendations = {
            "languages_to_learn": [],
            "skills_to_improve": [],
            "practice_suggestions": [],
            "resource_recommendations": []
        }
        
        # Analyze skill levels
        for language, skill_level in profile.skill_level.items():
            if skill_level < 0.5:
                recommendations["languages_to_learn"].append({
                    "language": language,
                    "current_level": skill_level,
                    "reason": f"Your {language} skills need improvement"
                })
        
        # Analyze query patterns
        if profile.behavior.query_patterns:
            most_common_queries = sorted(profile.behavior.query_patterns.items(), 
                                       key=lambda x: x[1], reverse=True)[:3]
            
            for query_type, count in most_common_queries:
                if query_type == "debugging":
                    recommendations["skills_to_improve"].append({
                        "skill": "debugging",
                        "reason": "You frequently ask debugging questions"
                    })
                elif query_type == "optimization":
                    recommendations["skills_to_improve"].append({
                        "skill": "optimization",
                        "reason": "You frequently ask about optimization"
                    })
        
        # Generate practice suggestions based on feedback
        if profile.behavior.feedback_history:
            recent_feedback = profile.behavior.feedback_history[-10:]
            
            # Analyze feedback patterns
            negative_feedback = [f for f in recent_feedback if f.get("rating", 0) < 3]
            
            if negative_feedback:
                recommendations["practice_suggestions"].append({
                    "area": "general improvement",
                    "reason": "Recent feedback suggests areas for improvement"
                })
        
        # Resource recommendations based on skill levels
        for language, skill_level in profile.skill_level.items():
            if skill_level < 0.3:
                recommendations["resource_recommendations"].append({
                    "language": language,
                    "level": "beginner",
                    "resources": [
                        f"Interactive {language} tutorial",
                        f"{language} basics course"
                    ]
                })
            elif 0.3 <= skill_level < 0.7:
                recommendations["resource_recommendations"].append({
                    "language": language,
                    "level": "intermediate",
                    "resources": [
                        f"Advanced {language} patterns",
                        f"{language} best practices"
                    ]
                })
            else:
                recommendations["resource_recommendations"].append({
                    "language": language,
                    "level": "advanced",
                    "resources": [
                        f"{language} design patterns",
                        f"Advanced {language} techniques"
                    ]
                })
        
        return recommendations
    
    def analyze_user_clusters(self) -> Dict[str, Any]:
        """Analyze user behavior clusters for system improvements"""
        if not self.profiles:
            return {"error": "No user profiles available"}
        
        # Extract features for clustering
        features = []
        user_ids = []
        
        for user_id, profile in self.profiles.items():
            feature_vector = [
                profile.preferences.complexity_tolerance,
                profile.behavior.completion_acceptance_rate or 0.5,
                len(profile.behavior.query_patterns),
                len(profile.behavior.feedback_history),
                sum(profile.skill_level.values()) / len(profile.skill_level)
            ]
            features.append(feature_vector)
            user_ids.append(user_id)
        
        # Normalize features
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features)
        
        # Cluster users
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(features_normalized)
        
        # Analyze clusters
        cluster_analysis = {}
        for cluster_id in range(3):
            cluster_users = [user_ids[i] for i, c in enumerate(clusters) if c == cluster_id]
            cluster_profiles = [self.profiles[uid] for uid in cluster_users]
            
            # Calculate cluster characteristics
            avg_complexity = np.mean([p.preferences.complexity_tolerance for p in cluster_profiles])
            avg_acceptance = np.mean([p.behavior.completion_acceptance_rate or 0.5 for p in cluster_profiles])
            avg_skill = np.mean([sum(p.skill_level.values()) / len(p.skill_level) for p in cluster_profiles])
            
            cluster_analysis[f"cluster_{cluster_id}"] = {
                "user_count": len(cluster_users),
                "avg_complexity_tolerance": avg_complexity,
                "avg_completion_acceptance": avg_acceptance,
                "avg_skill_level": avg_skill,
                "characteristics": self._describe_cluster(avg_complexity, avg_acceptance, avg_skill)
            }
        
        return {
            "cluster_analysis": cluster_analysis,
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "user_clusters": {user_ids[i]: int(clusters[i]) for i in range(len(user_ids))}
        }
    
    def _describe_cluster(self, complexity