# recommender/collaborative.py

class CollaborativeFiltering:
    def __init__(self, top_n=10):
        self.top_n = top_n
    
    def fit(self, **kwargs):
        """训练模型"""
        print("🔧 CollaborativeFiltering.fit()")
        return True
    
    def recommend(self, user_id=None):
        """生成推荐"""
        print(f"🔧 CollaborativeFiltering.recommend() - 用户ID: {user_id}")
        # 这里返回空列表，让HybridRecommender处理
        return []
