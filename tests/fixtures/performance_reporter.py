"""
Performance reporting utilities for generating comprehensive performance reports.

This module provides functionality to generate detailed performance reports
including trends, baselines, anomalies, and recommendations.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import asdict

from .performance_baselines import PerformanceBaselineManager
from .performance_statistics import PerformanceStatistics, TrendDirection


class PerformanceReporter:
    """Generates comprehensive performance reports."""
    
    def __init__(self, baseline_manager: Optional[PerformanceBaselineManager] = None):
        """Initialize performance reporter."""
        self.baseline_manager = baseline_manager or PerformanceBaselineManager()
        self.report_dir = Path("test_reports/performance")
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(self, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        timestamp = datetime.now(timezone.utc)
        
        if output_file is None:
            output_file = self.report_dir / f"performance_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get base report from baseline manager
        report = self.baseline_manager.generate_performance_report()
        
        # Enhance with detailed analysis
        report["detailed_analysis"] = self._generate_detailed_analysis()
        report["recommendations"] = self._generate_recommendations()
        report["anomaly_detection"] = self._detect_performance_anomalies()
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_file = output_file.with_suffix('.html')
        self._generate_html_report(report, html_file)
        
        return report   
 
    def _generate_detailed_analysis(self) -> Dict[str, Any]:
        """Generate detailed statistical analysis for each operation."""
        analysis = {}
        
        # Group measurements by operation
        operations = {}
        for measurement in self.baseline_manager._measurements:
            if measurement.success:
                if measurement.operation_name not in operations:
                    operations[measurement.operation_name] = []
                operations[measurement.operation_name].append(measurement.duration)
        
        # Analyze each operation
        for operation_name, durations in operations.items():
            if len(durations) >= 3:
                # Statistical summary
                summary = PerformanceStatistics.calculate_summary(durations)
                
                # Trend analysis
                trend = PerformanceStatistics.analyze_trend(durations)
                
                # Anomaly detection
                anomalies = PerformanceStatistics.detect_anomalies(durations, method="iqr")
                
                analysis[operation_name] = {
                    "statistical_summary": asdict(summary),
                    "trend_analysis": trend.to_dict(),
                    "anomaly_count": len(anomalies),
                    "anomalies": [asdict(anomaly) for anomaly in anomalies[:5]],  # Limit to 5
                    "stability_assessment": {
                        "is_stable": summary.is_stable(),
                        "coefficient_of_variation": summary.coefficient_of_variation(),
                        "stability_rating": self._get_stability_rating(summary.coefficient_of_variation())
                    }
                }
        
        return analysis
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Analyze each operation for recommendations
        for measurement in self.baseline_manager._measurements:
            operation_name = measurement.operation_name
            
            # Get recent measurements for this operation
            recent_measurements = [
                m.duration for m in self.baseline_manager._measurements[-50:]
                if m.operation_name == operation_name and m.success
            ]
            
            if len(recent_measurements) >= 5:
                summary = PerformanceStatistics.calculate_summary(recent_measurements)
                trend = PerformanceStatistics.analyze_trend(recent_measurements)
                
                # Generate recommendations based on analysis
                if trend.direction == TrendDirection.DEGRADING and trend.significance > 0.3:
                    recommendations.append({
                        "operation": operation_name,
                        "priority": "high",
                        "type": "performance_degradation",
                        "description": f"Performance degrading for {operation_name}",
                        "details": trend.explanation,
                        "suggested_actions": [
                            "Review recent code changes",
                            "Check for resource contention",
                            "Profile the operation for bottlenecks"
                        ]
                    })
                
                if not summary.is_stable():
                    recommendations.append({
                        "operation": operation_name,
                        "priority": "medium",
                        "type": "performance_instability",
                        "description": f"Unstable performance for {operation_name}",
                        "details": f"Coefficient of variation: {summary.coefficient_of_variation():.3f}",
                        "suggested_actions": [
                            "Investigate environmental factors",
                            "Check for resource competition",
                            "Consider performance optimization"
                        ]
                    })
                
                # Check if performance is significantly slower than baseline
                baseline = self.baseline_manager.get_baseline(operation_name)
                if baseline and summary.mean > baseline.baseline_time * 1.5:
                    recommendations.append({
                        "operation": operation_name,
                        "priority": "high",
                        "type": "baseline_deviation",
                        "description": f"Performance significantly slower than baseline for {operation_name}",
                        "details": f"Current: {summary.mean:.3f}s, Baseline: {baseline.baseline_time:.3f}s",
                        "suggested_actions": [
                            "Compare with baseline conditions",
                            "Check for system changes",
                            "Consider re-establishing baseline"
                        ]
                    })
        
        return recommendations
    
    def _detect_performance_anomalies(self) -> Dict[str, Any]:
        """Detect performance anomalies across all operations."""
        anomaly_report = {
            "total_anomalies": 0,
            "operations_with_anomalies": 0,
            "anomaly_details": {}
        }
        
        # Group measurements by operation
        operations = {}
        for measurement in self.baseline_manager._measurements:
            if measurement.success:
                if measurement.operation_name not in operations:
                    operations[measurement.operation_name] = []
                operations[measurement.operation_name].append(measurement.duration)
        
        # Detect anomalies for each operation
        for operation_name, durations in operations.items():
            if len(durations) >= 5:
                anomalies = PerformanceStatistics.detect_anomalies(durations, method="modified_zscore")
                
                if anomalies:
                    anomaly_report["operations_with_anomalies"] += 1
                    anomaly_report["total_anomalies"] += len(anomalies)
                    anomaly_report["anomaly_details"][operation_name] = {
                        "count": len(anomalies),
                        "anomalies": [asdict(anomaly) for anomaly in anomalies[:3]]  # Limit to 3
                    }
        
        return anomaly_report
    
    def _get_stability_rating(self, cv: float) -> str:
        """Get stability rating based on coefficient of variation."""
        if cv <= 0.1:
            return "excellent"
        elif cv <= 0.2:
            return "good"
        elif cv <= 0.3:
            return "fair"
        elif cv <= 0.5:
            return "poor"
        else:
            return "very_poor"
    
    def _generate_html_report(self, report_data: Dict[str, Any], output_file: Path) -> None:
        """Generate HTML version of the performance report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report - {report_data['generated_at']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
        .recommendation {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b6b; background-color: #fff5f5; }}
        .recommendation.medium {{ border-left-color: #ffa500; background-color: #fff8e1; }}
        .recommendation.low {{ border-left-color: #4caf50; background-color: #f1f8e9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Report</h1>
        <p>Generated: {report_data['generated_at']}</p>
        <p>System: {report_data['system_config']['cpu_cores']} cores, 
           {report_data['system_config']['memory_gb']:.1f}GB RAM</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="metric">
            <strong>Total Baselines:</strong> {report_data['summary']['total_baselines']}
        </div>
        <div class="metric">
            <strong>Total Measurements:</strong> {report_data['summary']['total_measurements']}
        </div>
        <div class="metric">
            <strong>Operations Tracked:</strong> {report_data['summary']['operations_tracked']}
        </div>
    </div>
"""
        
        # Add recommendations section
        if report_data.get('recommendations'):
            html_content += """
    <div class="section">
        <h2>Recommendations</h2>
"""
            for rec in report_data['recommendations']:
                priority_class = rec['priority']
                html_content += f"""
        <div class="recommendation {priority_class}">
            <h4>{rec['description']} ({rec['priority']} priority)</h4>
            <p>{rec['details']}</p>
            <ul>
"""
                for action in rec['suggested_actions']:
                    html_content += f"                <li>{action}</li>\n"
                html_content += """
            </ul>
        </div>
"""
            html_content += "    </div>\n"
        
        # Add baselines table
        if report_data.get('baselines'):
            html_content += """
    <div class="section">
        <h2>Performance Baselines</h2>
        <table>
            <tr>
                <th>Operation</th>
                <th>Baseline Time (s)</th>
                <th>Std Deviation</th>
                <th>Sample Count</th>
                <th>Created</th>
            </tr>
"""
            for operation, baseline in report_data['baselines'].items():
                html_content += f"""
            <tr>
                <td>{operation}</td>
                <td>{baseline['baseline_time']:.3f}</td>
                <td>{baseline['std_deviation']:.3f}</td>
                <td>{baseline['sample_count']}</td>
                <td>{baseline['created_at'][:10]}</td>
            </tr>
"""
            html_content += """
        </table>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def generate_trend_report(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate trend-focused performance report."""
        trend_report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": days_back,
            "trends": {}
        }
        
        # Get all unique operations
        operations = set(m.operation_name for m in self.baseline_manager._measurements)
        
        for operation in operations:
            trend_data = self.baseline_manager.get_performance_trends(operation, days_back)
            if "error" not in trend_data:
                trend_report["trends"][operation] = trend_data
        
        return trend_report