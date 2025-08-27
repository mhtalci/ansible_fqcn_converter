"""
Statistical analysis utilities for performance validation.

This module provides statistical methods for analyzing performance data,
detecting anomalies, and validating performance against baselines.
"""

import statistics
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Performance trend direction."""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class StatisticalSummary:
    """Statistical summary of performance measurements."""
    count: int
    mean: float
    median: float
    std_deviation: float
    variance: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    percentile_99: float
    
    def coefficient_of_variation(self) -> float:
        """Calculate coefficient of variation (std_dev / mean)."""
        return self.std_deviation / self.mean if self.mean > 0 else float('inf')
    
    def is_stable(self, cv_threshold: float = 0.3) -> bool:
        """Check if measurements are stable based on coefficient of variation."""
        return self.coefficient_of_variation() <= cv_threshold


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection analysis."""
    is_anomaly: bool
    anomaly_score: float
    threshold: float
    method: str
    explanation: str


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    direction: TrendDirection
    slope: float
    correlation: float
    significance: float
    confidence_interval: Tuple[float, float]
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "direction": self.direction.value,
            "slope": self.slope,
            "correlation": self.correlation,
            "significance": self.significance,
            "confidence_interval": list(self.confidence_interval),
            "explanation": self.explanation
        }


class PerformanceStatistics:
    """Statistical analysis utilities for performance data."""
    
    @staticmethod
    def calculate_summary(measurements: List[float]) -> StatisticalSummary:
        """Calculate comprehensive statistical summary."""
        if not measurements:
            raise ValueError("Cannot calculate statistics for empty measurement list")
        
        sorted_measurements = sorted(measurements)
        n = len(measurements)
        
        return StatisticalSummary(
            count=n,
            mean=statistics.mean(measurements),
            median=statistics.median(measurements),
            std_deviation=statistics.stdev(measurements) if n > 1 else 0.0,
            variance=statistics.variance(measurements) if n > 1 else 0.0,
            min_value=min(measurements),
            max_value=max(measurements),
            percentile_25=PerformanceStatistics._percentile(sorted_measurements, 25),
            percentile_75=PerformanceStatistics._percentile(sorted_measurements, 75),
            percentile_95=PerformanceStatistics._percentile(sorted_measurements, 95),
            percentile_99=PerformanceStatistics._percentile(sorted_measurements, 99)
        )
    
    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        
        k = (len(sorted_data) - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_data[int(k)]
        
        d0 = sorted_data[int(f)] * (c - k)
        d1 = sorted_data[int(c)] * (k - f)
        return d0 + d1
    
    @staticmethod
    def detect_anomalies(measurements: List[float], 
                        method: str = "iqr") -> List[AnomalyDetectionResult]:
        """Detect anomalies in performance measurements."""
        if len(measurements) < 3:
            return []
        
        results = []
        
        if method == "iqr":
            results.extend(PerformanceStatistics._detect_iqr_anomalies(measurements))
        elif method == "zscore":
            results.extend(PerformanceStatistics._detect_zscore_anomalies(measurements))
        elif method == "modified_zscore":
            results.extend(PerformanceStatistics._detect_modified_zscore_anomalies(measurements))
        else:
            raise ValueError(f"Unknown anomaly detection method: {method}")
        
        return results
    
    @staticmethod
    def _detect_iqr_anomalies(measurements: List[float]) -> List[AnomalyDetectionResult]:
        """Detect anomalies using Interquartile Range method."""
        summary = PerformanceStatistics.calculate_summary(measurements)
        
        iqr = summary.percentile_75 - summary.percentile_25
        lower_bound = summary.percentile_25 - 1.5 * iqr
        upper_bound = summary.percentile_75 + 1.5 * iqr
        
        results = []
        for i, measurement in enumerate(measurements):
            is_anomaly = measurement < lower_bound or measurement > upper_bound
            if is_anomaly:
                if measurement < lower_bound:
                    score = (lower_bound - measurement) / iqr if iqr > 0 else 0
                    explanation = f"Measurement {measurement:.3f} is {score:.2f} IQRs below lower bound {lower_bound:.3f}"
                else:
                    score = (measurement - upper_bound) / iqr if iqr > 0 else 0
                    explanation = f"Measurement {measurement:.3f} is {score:.2f} IQRs above upper bound {upper_bound:.3f}"
                
                results.append(AnomalyDetectionResult(
                    is_anomaly=True,
                    anomaly_score=score,
                    threshold=1.5,
                    method="iqr",
                    explanation=explanation
                ))
        
        return results
    
    @staticmethod
    def _detect_zscore_anomalies(measurements: List[float], 
                                threshold: float = 2.0) -> List[AnomalyDetectionResult]:
        """Detect anomalies using Z-score method."""
        if len(measurements) < 2:
            return []
        
        mean_val = statistics.mean(measurements)
        std_val = statistics.stdev(measurements)
        
        if std_val == 0:
            return []
        
        results = []
        for measurement in measurements:
            z_score = abs(measurement - mean_val) / std_val
            is_anomaly = z_score > threshold
            
            if is_anomaly:
                explanation = f"Measurement {measurement:.3f} has Z-score {z_score:.2f} > threshold {threshold}"
                results.append(AnomalyDetectionResult(
                    is_anomaly=True,
                    anomaly_score=z_score,
                    threshold=threshold,
                    method="zscore",
                    explanation=explanation
                ))
        
        return results
    
    @staticmethod
    def _detect_modified_zscore_anomalies(measurements: List[float],
                                        threshold: float = 3.5) -> List[AnomalyDetectionResult]:
        """Detect anomalies using Modified Z-score method (more robust)."""
        if len(measurements) < 2:
            return []
        
        median_val = statistics.median(measurements)
        mad = statistics.median([abs(x - median_val) for x in measurements])
        
        if mad == 0:
            return []
        
        results = []
        for measurement in measurements:
            modified_z_score = 0.6745 * (measurement - median_val) / mad
            is_anomaly = abs(modified_z_score) > threshold
            
            if is_anomaly:
                explanation = f"Measurement {measurement:.3f} has Modified Z-score {modified_z_score:.2f} > threshold {threshold}"
                results.append(AnomalyDetectionResult(
                    is_anomaly=True,
                    anomaly_score=abs(modified_z_score),
                    threshold=threshold,
                    method="modified_zscore",
                    explanation=explanation
                ))
        
        return results
    
    @staticmethod
    def analyze_trend(measurements: List[float]) -> TrendAnalysis:
        """Analyze performance trend using linear regression."""
        if len(measurements) < 3:
            return TrendAnalysis(
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=0.0,
                correlation=0.0,
                significance=0.0,
                confidence_interval=(0.0, 0.0),
                explanation="Insufficient data for trend analysis"
            )
        
        # Prepare data for linear regression
        x_values = list(range(len(measurements)))
        y_values = measurements
        
        # Calculate linear regression
        n = len(measurements)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        # Calculate slope and correlation
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            slope = 0.0
            correlation = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Calculate correlation coefficient
            numerator = n * sum_xy - sum_x * sum_y
            denom_x = math.sqrt(n * sum_x2 - sum_x * sum_x)
            denom_y = math.sqrt(n * sum_y2 - sum_y * sum_y)
            
            if denom_x == 0 or denom_y == 0:
                correlation = 0.0
            else:
                correlation = numerator / (denom_x * denom_y)
        
        # Determine trend direction
        if abs(slope) < 0.001:  # Very small slope considered stable
            direction = TrendDirection.STABLE
        elif slope < 0:
            direction = TrendDirection.IMPROVING  # Decreasing time is improving
        else:
            direction = TrendDirection.DEGRADING  # Increasing time is degrading
        
        # Calculate significance (simplified t-test)
        if n > 2:
            # Standard error of slope
            y_mean = sum_y / n
            residual_sum_squares = sum((y - (slope * x + (y_mean - slope * sum_x / n)))**2 
                                     for x, y in zip(x_values, y_values))
            
            if residual_sum_squares > 0 and denominator > 0:
                standard_error = math.sqrt(residual_sum_squares / (n - 2)) / math.sqrt(denominator / n)
                t_statistic = abs(slope / standard_error) if standard_error > 0 else 0
                # Simplified significance: t > 2 is roughly p < 0.05 for small samples
                significance = min(1.0, t_statistic / 2.0)
            else:
                significance = 0.0
        else:
            significance = 0.0
        
        # Calculate confidence interval for slope (simplified)
        if n > 2 and significance > 0:
            margin_of_error = 2.0 * (abs(slope) / significance) if significance > 0 else abs(slope)
            confidence_interval = (slope - margin_of_error, slope + margin_of_error)
        else:
            confidence_interval = (slope, slope)
        
        # Generate explanation
        if direction == TrendDirection.STABLE:
            explanation = f"Performance is stable (slope: {slope:.6f})"
        elif direction == TrendDirection.IMPROVING:
            explanation = f"Performance is improving (slope: {slope:.6f}, correlation: {correlation:.3f})"
        else:
            explanation = f"Performance is degrading (slope: {slope:.6f}, correlation: {correlation:.3f})"
        
        if significance > 0.5:
            explanation += " - trend is statistically significant"
        elif significance > 0.2:
            explanation += " - trend has moderate significance"
        else:
            explanation += " - trend is not statistically significant"
        
        return TrendAnalysis(
            direction=direction,
            slope=slope,
            correlation=correlation,
            significance=significance,
            confidence_interval=confidence_interval,
            explanation=explanation
        )
    
    @staticmethod
    def compare_distributions(baseline_measurements: List[float],
                            current_measurements: List[float]) -> Dict[str, Any]:
        """Compare two distributions of performance measurements."""
        if not baseline_measurements or not current_measurements:
            return {"error": "Cannot compare empty measurement lists"}
        
        baseline_summary = PerformanceStatistics.calculate_summary(baseline_measurements)
        current_summary = PerformanceStatistics.calculate_summary(current_measurements)
        
        # Calculate effect size (Cohen's d)
        pooled_std = math.sqrt(
            ((len(baseline_measurements) - 1) * baseline_summary.variance +
             (len(current_measurements) - 1) * current_summary.variance) /
            (len(baseline_measurements) + len(current_measurements) - 2)
        )
        
        cohens_d = (current_summary.mean - baseline_summary.mean) / pooled_std if pooled_std > 0 else 0
        
        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_interpretation = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_interpretation = "small"
        elif abs(cohens_d) < 0.8:
            effect_interpretation = "medium"
        else:
            effect_interpretation = "large"
        
        # Calculate percentage change
        percent_change = ((current_summary.mean - baseline_summary.mean) / 
                         baseline_summary.mean * 100) if baseline_summary.mean > 0 else 0
        
        return {
            "baseline_summary": baseline_summary,
            "current_summary": current_summary,
            "mean_difference": current_summary.mean - baseline_summary.mean,
            "percent_change": percent_change,
            "cohens_d": cohens_d,
            "effect_size": effect_interpretation,
            "performance_change": "improved" if cohens_d < -0.2 else "degraded" if cohens_d > 0.2 else "unchanged"
        }