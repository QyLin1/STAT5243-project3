import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("pastel")
plt.rcParams['figure.figsize'] = [12, 8]  # Set larger figure size
plt.rcParams['font.size'] = 12  # Increase font size

# Create a results directory
results_dir = 'AB_Test_Results/'
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

# Function to check normality
def check_normality(data, group_col, metric_col):
    group1 = data[data[group_col] == data[group_col].unique()[0]][metric_col]
    group2 = data[data[group_col] == data[group_col].unique()[1]][metric_col]
    
    # Shapiro-Wilk test
    _, p_val1 = stats.shapiro(group1) if len(group1) < 5000 else (0, 0)
    _, p_val2 = stats.shapiro(group2) if len(group2) < 5000 else (0, 0)
    
    # For large samples, Shapiro test might not be reliable, so use a combination of approaches
    if len(group1) >= 5000 or len(group2) >= 5000:
        return False  # For large samples, just use non-parametric test
    
    return p_val1 > 0.05 and p_val2 > 0.05

# Function to perform statistical test
def perform_statistical_test(data, group_col, metric_col):
    group1 = data[data[group_col] == data[group_col].unique()[0]][metric_col]
    group2 = data[data[group_col] == data[group_col].unique()[1]][metric_col]
    
    # Check for normality
    is_normal = check_normality(data, group_col, metric_col)
    
    if is_normal:
        # Perform t-test
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
        test_name = "t-test"
    else:
        # Perform Mann-Whitney U test
        u_stat, p_val = stats.mannwhitneyu(group1, group2)
        test_name = "Mann-Whitney U test"
    
    return p_val, test_name, is_normal

# Function to create comparison plot
def create_comparison_plot(data, group_col, metric_col, metric_name):
    # Create figure with increased height for better text spacing
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Calculate means for plotting
    means = data.groupby(group_col)[metric_col].mean().reset_index()
    
    # Also calculate medians
    medians = data.groupby(group_col)[metric_col].median().reset_index()
    
    # Get descriptive statistics
    stats_by_group = data.groupby(group_col)[metric_col].describe()
    
    # Perform statistical test
    p_val, test_name, is_normal = perform_statistical_test(data, group_col, metric_col)
    
    # Create bar plot with increased width between bars
    bars = sns.barplot(x=group_col, y=metric_col, data=means, ax=ax, palette="Set2", width=0.6)
    
    # Calculate y-axis limits for better spacing
    y_max = max(means[metric_col].max(), medians[metric_col].max())
    y_min = min(means[metric_col].min(), medians[metric_col].min())
    y_range = y_max - y_min
    
    # Set y-axis limits with padding
    ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.4 * y_range)
    
    # Add significance annotation with adjusted position
    if p_val < 0.05:
        if p_val < 0.001:
            significance = "***"
        elif p_val < 0.01:
            significance = "**"
        else:
            significance = "*"
        
        y_pos = y_max + 0.15 * y_range
        ax.text(0.5, y_pos, significance, 
                horizontalalignment='center', size=24, color='red')
    
    # Add labels with increased font sizes
    plt.title(f'Comparison of {metric_name} between Groups\n({test_name}, p={p_val:.4f})', 
             fontsize=20, pad=20)
    plt.xlabel('Group', fontsize=18)
    plt.ylabel(metric_name, fontsize=18)
    
    # Increase tick label sizes
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    
    # Add actual values on bars with adjusted positions
    for i, (mean_val, median_val) in enumerate(zip(means[metric_col], medians[metric_col])):
        # Position mean and median labels with better spacing
        mean_y = mean_val + 0.02 * y_range
        median_y = mean_val + 0.08 * y_range
        
        ax.text(i, mean_y, f'Mean: {mean_val:.4f}', 
                ha='center', fontsize=16, color='black')
        ax.text(i, median_y, f'Median: {median_val:.4f}', 
                ha='center', fontsize=16, color='black')
    
    # Add detailed statistics as text with improved formatting and position
    textstr = '\n'.join([
        f"Normality assumption {'met' if is_normal else 'not met'}",
        f"Statistical test used: {test_name}",
        f"p-value: {p_val:.4f}",
        f"Significant difference: {'Yes' if p_val < 0.05 else 'No'}"
    ])
    
    # Add a box for the statistics with adjusted position and style
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray')
    ax.text(0.05, 0.98, textstr, transform=ax.transAxes, fontsize=16,
            verticalalignment='top', bbox=props)
    
    # Save figure to results directory with improved resolution
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to prevent text cutoff
    save_path = os.path.join(results_dir, f'{metric_col}_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    print(f"Plot saved to: {save_path}")
    
    # Close the plot to free memory
    plt.close(fig)
    
    # Get group means for interpretation
    red_mean = means[means[group_col] == 'red'][metric_col].values[0]
    gray_mean = means[means[group_col] == 'gray'][metric_col].values[0]
    better_group = 'red' if red_mean > gray_mean else 'gray'
    
    # For error metrics, lower is better
    if 'error' in metric_col.lower():
        better_group = 'red' if red_mean < gray_mean else 'gray'
    
    percent_diff = abs(red_mean - gray_mean) / ((red_mean + gray_mean) / 2) * 100
    
    # Return full stats for reporting
    return {
        'metric': metric_name,
        'p_value': p_val,
        'test_name': test_name,
        'is_normal': is_normal,
        'is_significant': p_val < 0.05,
        'stats_by_group': stats_by_group,
        'red_mean': red_mean,
        'gray_mean': gray_mean,
        'better_group': better_group,
        'percent_diff': percent_diff
    }

# Function to interpret results and draw conclusions
def draw_conclusions(results):
    conclusions = []
    print("\n=== CONCLUSIONS ===")
    print("--------------------")
    
    # General conclusion pattern
    for result in results:
        metric = result['metric']
        is_significant = result['is_significant']
        better_group = result['better_group']
        red_mean = result['red_mean']
        gray_mean = result['gray_mean']
        percent_diff = result['percent_diff']
        
        # Create conclusion text
        if is_significant:
            if 'Error' in metric:
                conclusion = f"Users are {percent_diff:.1f}% more likely to make errors under the '{better_group}' group compared to the {'gray' if better_group == 'red' else 'red'} group. "
                if better_group == 'red':
                    conclusion += f"Red interface shows significantly LOWER {metric.lower()} ({red_mean:.4f} vs {gray_mean:.4f})."
                else:
                    conclusion += f"Gray interface shows significantly LOWER {metric.lower()} ({gray_mean:.4f} vs {red_mean:.4f})."
            else:
                conclusion = f"The '{better_group}' group performs {percent_diff:.1f}% better in terms of {metric.lower()} compared to the {'gray' if better_group == 'red' else 'red'} group. "
                if better_group == 'red':
                    conclusion += f"Red interface shows significantly HIGHER {metric.lower()} ({red_mean:.4f} vs {gray_mean:.4f})."
                else:
                    conclusion += f"Gray interface shows significantly HIGHER {metric.lower()} ({gray_mean:.4f} vs {red_mean:.4f})."
        else:
            conclusion = f"There is no statistically significant difference in {metric.lower()} between the red and gray groups "
            conclusion += f"(red: {red_mean:.4f} vs gray: {gray_mean:.4f}, p-value: {result['p_value']:.4f})."
        
        conclusions.append(conclusion)
        print(f"• {conclusion}")
    
    # Overall recommendation
    significant_results = [r for r in results if r['is_significant']]
    
    if significant_results:
        # Count which group performed better in significant metrics
        red_better_count = sum(1 for r in significant_results if r['better_group'] == 'red')
        gray_better_count = len(significant_results) - red_better_count
        
        print("\n=== OVERALL RECOMMENDATION ===")
        if red_better_count > gray_better_count:
            print(f"The RED interface appears to perform better overall, winning in {red_better_count} out of {len(significant_results)} significant metrics.")
        elif gray_better_count > red_better_count:
            print(f"The GRAY interface appears to perform better overall, winning in {gray_better_count} out of {len(significant_results)} significant metrics.")
        else:
            print("Both RED and GRAY interfaces have equal performance across the metrics showing significant differences.")
    else:
        print("\n=== OVERALL RECOMMENDATION ===")
        print("No statistically significant differences were found between the RED and GRAY groups for any of the metrics analyzed.")
    
    # Return conclusions as a list of strings for saving to file
    return conclusions

# Function to create aggregated comparison plot
def create_aggregated_comparison_plot(data, metrics):
    # Create figure
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Prepare data for plotting
    plot_data = []
    for metric_col, metric_name in metrics:
        # Calculate means for both groups
        means = data.groupby('group')[metric_col].mean()
        # Normalize the values to make them comparable
        max_val = data[metric_col].max()
        min_val = data[metric_col].min()
        normalized_means = (means - min_val) / (max_val - min_val)
        
        for group in ['red', 'gray']:
            plot_data.append({
                'Metric': metric_name,
                'Group': group,
                'Normalized Value': normalized_means[group],
                'Original Value': means[group]
            })
    
    # Convert to DataFrame
    plot_df = pd.DataFrame(plot_data)
    
    # Create grouped bar plot
    sns.barplot(x='Metric', y='Normalized Value', hue='Group', data=plot_df, ax=ax, palette=['red', 'gray'])
    
    # Customize the plot with larger text sizes
    plt.title('Comparison of All Metrics Between Groups (Normalized Values)', fontsize=20, pad=20)
    plt.xlabel('Metrics', fontsize=20)
    plt.ylabel('Normalized Value', fontsize=20)
    
    # Increase tick label sizes
    plt.xticks(rotation=45, ha='right', fontsize=18)
    plt.yticks(fontsize=16)
    
    # Increase legend text size
    plt.legend(fontsize=20)
    
    # Add value labels on the bars with larger font
    for i, row in enumerate(plot_df.itertuples()):
        ax.text(i // 2, row._3, f'{row._4:.3f}', 
                ha='center', va='bottom', fontsize=18)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    save_path = os.path.join(results_dir, 'aggregated_metrics_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nAggregated comparison plot saved to: {save_path}")
    
    # Close the plot
    plt.close(fig)

# Main analysis function
def analyze_ab_test():
    print("Starting AB Test Analysis...")
    print("===========================\n")
    
    try:
        # Load the dataset - Updated file path
        print("Loading data from: ab_test_log_step3_cleaned.csv")
        data = pd.read_csv('ab_test_log_step3_cleaned.csv')
        
        print("\nData loaded successfully!")
        print(f"Dataset shape: {data.shape}")
        print("\nFirst few rows:")
        print(data.head())
        
        print("\nData columns:")
        print(data.columns.tolist())
        
        # Check if the required columns exist
        required_metrics = [
            'group', 
            'total_clicked_rate', 
            'total_clicked_count', 
            'total_session_time', 
            'total_error_count', 
            'total_error_rate'
        ]
        
        missing_cols = [col for col in required_metrics if col not in data.columns]
        
        if missing_cols:
            print(f"\nWARNING: The following required columns are missing: {missing_cols}")
            print("Please check the column names in your dataset.")
            return
        
        # Display group information
        print("\nGroup distribution:")
        print(data['group'].value_counts())
        
        # Define metrics to analyze
        metrics = [
            ('total_clicked_rate', 'Clicked Rate'),
            ('total_clicked_count', 'Clicked Count'),
            ('total_session_time', 'Session Time (seconds)'),
            ('total_error_count', 'Error Count'),
            ('total_error_rate', 'Error Rate')
        ]
        
        # Analyze each metric
        print("\n=== ANALYSIS RESULTS ===")
        print("\nStatistical Tests Summary:")
        print("-------------------------")
        
        all_results = []
        
        for metric_col, metric_name in metrics:
            print(f"\nAnalyzing {metric_name}...")
            result = create_comparison_plot(data, 'group', metric_col, metric_name)
            all_results.append(result)
            
            # Print detailed result
            print(f"  • {metric_name}: {result['test_name']}, p-value = {result['p_value']:.4f}")
            print(f"    Significant difference: {'Yes' if result['is_significant'] else 'No'}")
            print(f"    Normality assumption: {'Met' if result['is_normal'] else 'Not met'}")
            print("\n    Descriptive statistics by group:")
            print(result['stats_by_group'])
        
        # Create summary table
        print("\n=== SUMMARY TABLE ===")
        summary_results = []
        for result in all_results:
            summary_results.append({
                'Metric': result['metric'],
                'Test': result['test_name'],
                'p-value': result['p_value'],
                'Significant': result['is_significant'],
                'Red Mean': result['red_mean'],
                'Gray Mean': result['gray_mean'],
                'Better Group': result['better_group'] if result['is_significant'] else 'No difference',
                'Normality Assumption Met': result['is_normal']
            })
        
        results_df = pd.DataFrame(summary_results)
        print(results_df)
        
        # Save summary results to CSV
        csv_path = os.path.join(results_dir, 'ab_test_analysis_results.csv')
        results_df.to_csv(csv_path, index=False)
        
        # Create aggregated comparison plot
        create_aggregated_comparison_plot(data, metrics)
        
        # Draw conclusions based on the analysis
        conclusions = draw_conclusions(all_results)
        
        # Save conclusions to a text file
        conclusions_path = os.path.join(results_dir, 'ab_test_conclusions.txt')
        with open(conclusions_path, 'w') as f:
            f.write("=== AB TEST ANALYSIS CONCLUSIONS ===\n\n")
            for i, conclusion in enumerate(conclusions, 1):
                f.write(f"{i}. {conclusion}\n\n")
            
            # Add overall recommendation
            significant_results = [r for r in all_results if r['is_significant']]
            if significant_results:
                red_better_count = sum(1 for r in significant_results if r['better_group'] == 'red')
                gray_better_count = len(significant_results) - red_better_count
                
                f.write("\n=== OVERALL RECOMMENDATION ===\n")
                if red_better_count > gray_better_count:
                    f.write(f"The RED interface appears to perform better overall, winning in {red_better_count} out of {len(significant_results)} significant metrics.")
                elif gray_better_count > red_better_count:
                    f.write(f"The GRAY interface appears to perform better overall, winning in {gray_better_count} out of {len(significant_results)} significant metrics.")
                else:
                    f.write("Both RED and GRAY interfaces have equal performance across the metrics showing significant differences.")
            else:
                f.write("\n=== OVERALL RECOMMENDATION ===\n")
                f.write("No statistically significant differences were found between the RED and GRAY groups for any of the metrics analyzed.")
        
        print(f"\nResults saved to CSV: {csv_path}")
        print(f"Conclusions saved to: {conclusions_path}")
        print(f"All plots saved to: {results_dir}")
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")

if __name__ == "__main__":
    analyze_ab_test() 