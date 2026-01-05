"""
推荐算法评估模块
"""
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics import precision_score, recall_score, f1_score, ndcg_score
from database.db_operations import get_user_play_history

class RecommenderEvaluator:
    """推荐算法评估器"""
    
    def __init__(self, test_ratio: float = 0.2):
        self.test_ratio = test_ratio
    
    def split_train_test(self, user_history: List[Dict]) -> tuple:
        """划分训练集和测试集"""
        if not user_history:
            return [], []
        
        # 按时间排序
        sorted_history = sorted(user_history, key=lambda x: x.get('timestamp', 0))
        
        # 划分
        split_idx = int(len(sorted_history) * (1 - self.test_ratio))
        train_set = sorted_history[:split_idx]
        test_set = sorted_history[split_idx:]
        
        return train_set, test_set
    
    def evaluate_precision_recall(self, recommendations: List[int], ground_truth: List[int], k: int = 10):
        """评估精确率和召回率"""
        if k > len(recommendations):
            k = len(recommendations)
        
        # 获取top-k推荐
        top_k_recs = recommendations[:k]
        
        # 计算相关物品
        relevant_items = set(ground_truth)
        recommended_items = set(top_k_recs)
        
        # 计算交集
        true_positives = len(relevant_items.intersection(recommended_items))
        
        # 精确率 = TP / (TP + FP)
        precision = true_positives / k if k > 0 else 0
        
        # 召回率 = TP / (TP + FN)
        recall = true_positives / len(relevant_items) if len(relevant_items) > 0 else 0
        
        # F1分数
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision@k': precision,
            'recall@k': recall,
            'f1_score@k': f1,
            'true_positives': true_positives,
            'k': k
        }
    
    def evaluate_ndcg(self, recommendations: List[int], ground_truth: List[int], k: int = 10):
        """评估NDCG"""
        if not ground_truth:
            return 0
        
        # 创建相关性分数列表
        y_true = [[1 if item in ground_truth else 0 for item in ground_truth]]
        y_score = [[1 if item in recommendations else 0 for item in ground_truth]]
        
        # 计算NDCG
        try:
            ndcg = ndcg_score(y_true, y_score, k=k)
        except:
            ndcg = 0
        
        return ndcg
    
    def evaluate_coverage(self, recommendations: List[List[int]], all_items: List[int]):
        """评估覆盖率"""
        if not recommendations:
            return 0
        
        # 统计所有被推荐的物品
        recommended_items = set()
        for rec_list in recommendations:
            recommended_items.update(rec_list)
        
        # 覆盖率 = 被推荐的物品数 / 总物品数
        coverage = len(recommended_items) / len(all_items) if len(all_items) > 0 else 0
        
        return coverage
    
    def evaluate_diversity(self, recommendations: List[List[int]], item_features: Dict[int, List]):
        """评估多样性"""
        if not recommendations or not item_features:
            return 0
        
        # 计算推荐列表间的平均相似度
        total_similarity = 0
        count = 0
        
        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):
                rec_i = recommendations[i]
                rec_j = recommendations[j]
                
                # 计算两个推荐列表的平均相似度
                list_similarity = self.calculate_list_similarity(rec_i, rec_j, item_features)
                total_similarity += list_similarity
                count += 1
        
        avg_similarity = total_similarity / count if count > 0 else 0
        
        # 多样性 = 1 - 平均相似度
        diversity = 1 - avg_similarity
        
        return diversity
    
    def calculate_list_similarity(self, list1: List[int], list2: List[int], 
                                  item_features: Dict[int, List]) -> float:
        """计算两个列表的相似度"""
        if not list1 or not list2:
            return 0
        
        # 计算所有物品对之间的相似度
        total_similarity = 0
        count = 0
        
        for item1 in list1:
            for item2 in list2:
                if item1 in item_features and item2 in item_features:
                    feat1 = item_features[item1]
                    feat2 = item_features[item2]
                    
                    # 计算余弦相似度
                    similarity = self.cosine_similarity(feat1, feat2)
                    total_similarity += similarity
                    count += 1
        
        return total_similarity / count if count > 0 else 0
    
    def cosine_similarity(self, vec1: List, vec2: List) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def evaluate_recommender(self, recommender, user_ids: List[int], 
                            all_song_ids: List[int], k: int = 10) -> Dict[str, Any]:
        """综合评估推荐算法"""
        results = {
            'precision': [],
            'recall': [],
            'f1': [],
            'ndcg': [],
            'coverage': None,
            'diversity': None
        }
        
        all_recommendations = []
        
        for user_id in user_ids:
            # 获取用户真实偏好（播放历史）
            history = get_user_play_history(user_id)
            ground_truth = [h.song_id for h in history]
            
            if not ground_truth:
                continue
            
            # 生成推荐
            recommendations = [rec['id'] for rec in recommender.recommend(user_id)]
            
            if not recommendations:
                continue
            
            # 评估单个用户
            metrics = self.evaluate_precision_recall(recommendations, ground_truth, k)
            ndcg = self.evaluate_ndcg(recommendations, ground_truth, k)
            
            results['precision'].append(metrics['precision@k'])
            results['recall'].append(metrics['recall@k'])
            results['f1'].append(metrics['f1_score@k'])
            results['ndcg'].append(ndcg)
            
            all_recommendations.append(recommendations[:k])
        
        # 计算平均指标
        avg_results = {}
        for key in ['precision', 'recall', 'f1', 'ndcg']:
            if results[key]:
                avg_results[f'avg_{key}'] = np.mean(results[key])
                avg_results[f'std_{key}'] = np.std(results[key])
            else:
                avg_results[f'avg_{key}'] = 0
                avg_results[f'std_{key}'] = 0
        
        # 评估覆盖率和多样性
        if all_recommendations and all_song_ids:
            # 这里需要物品特征数据来评估多样性
            # 暂时跳过多样性评估
            coverage = self.evaluate_coverage(all_recommendations, all_song_ids)
            avg_results['coverage'] = coverage
            avg_results['diversity'] = 0  # 需要物品特征数据
        
        return avg_results