# STAT5243-project3
project3 - A/B test
下面是为你两个文件夹编写的详细 README 文件，突出你进行的 A/B 测试实验和日志记录方式。

---

### 📁 `STAT5243_project_2`
**Description:**  
这是一个基于 [Python Shiny](https://shiny.posit.co/py/) 实现的交互式数据清洗与特征工程平台，主要用于执行 A/B 测试实验。实验核心目标是测试提示文本颜色（如红色 vs 黑色）对用户行为的影响。

**🔬 A/B Testing Objective:**  
我们将 Note 的提示颜色（例如 `红色` vs `黑色`）作为实验变量，随机分配用户至 A/B 两组：

- **Group A:** 显示红色提示文本（默认样式）
- **Group B:** 显示黑色提示文本（去强调）

**🎯 测量指标：**

每个用户会话通过日志系统记录以下操作行为指标：

- `apply_fe_button_clicked_count`: 应用了特征工程的点击次数
- `apply_fe_button_error_count`: 点击时出错次数
- `revert_button_clicked_count`: 撤销修改点击次数
- `download_button_clicked_count`: 下载数据的点击次数
- `download_button_clicked_time`: 下载按钮首次点击时间
- `*_clicked_rate`: 每个按钮点击次数 / 总会话时间
- `session_start_time`, `session_end_time`, `total_session_time`

数据会被写入本地 CSV 文件 `session_log.csv`，也可以通过 HTTP POST 发送至日志服务器。

**🧩 功能模块：**

- 数据文件上传与内置数据加载（支持 CSV, Excel, JSON, RDS 等）
- 变量选择与数据清洗
- 缺失值处理（转为 NA、均值/众数填充、列表删除）
- 特征工程操作（归一化、独热编码、日期转天数、Box-Cox 转换）
- 可视化（线图、柱图、散点图、直方图、相关热力图）
- 日志系统自动记录用户行为数据用于实验评估

---

### 📁 `STAT5243_log_server`
**Description:**  
这是配套的 Flask 服务器端，用于接收并存储前端 Shiny 应用中发起的日志数据。

**🔧 技术细节：**

- 使用 Flask 提供 `/log` 路由接收 JSON 日志 POST 请求
- 日志内容包括用户 ID、分组、按钮点击数、点击时间、总会话时间等
- 所有日志统一存储在 `server_log.csv` 中

**🚀 启动方式：**

```bash
cd STAT5243_log_server
python log_server.py
```

启动后将监听 `http://127.0.0.1:5000/log`，并等待来自前端应用的日志上传。

---

--------------------------------------------------------

Statistical Analysis - Nan Xiao

Summarization of the steps:
We've created a Python script for analyzing an AB test dataset comparing "red" and "gray" groups.
The script performs the following analysis for each metric:
Computes descriptive statistics for each group
Tests for normality to decide which statistical test to use
Performs either t-tests (for normal data) or Mann-Whitney U tests (for non-normal data)
Creates bar plots comparing the groups with significance indicators
Adds detailed statistics and test results on the plots
The script saves all plots to a dedicated directory (C:/Users/凡曲/AB_Test_Results) and also attempts to display them in windows.
A summary CSV file with all statistical test results is also saved.

Summary of Analysis Results
Based on the analysis of the AB test data comparing "red" and "gray" groups, here are the key findings:
Clicked Rate: No statistically significant difference between red and gray groups (p=0.3584)
Clicked Count: Statistically significant difference (p=0.0211)
Gray group has higher clicked count (7.94 vs 6.81)
Gray interface performs 15.4% better in this metric
Session Time: No statistically significant difference (p=0.6929)
Error Count: Statistically significant difference (p<0.0001)
Red group has lower error count (0.47 vs 1.10)
Users are 80.3% less likely to make errors with the red interface
Error Rate: Statistically significant difference (p=0.0001)
Red group has lower error rate (0.0037 vs 0.0065)
Users show 54.9% lower error rate with the red interface
Overall Conclusion
The red interface appears to perform better overall, winning in 2 out of 3 significant metrics (error count and error rate). While the gray interface leads in clicked count, the red interface demonstrates superior performance in reducing errors.
The analysis shows that:
Users click more with the gray interface
Users make fewer errors with the red interface
Session time isn't significantly different between interfaces
Recommendation
Based on the analysis, the red interface would be the recommended choice if minimizing errors is the primary goal. However, if higher engagement (more clicks) is prioritized, the gray interface might be preferred.
All the plots, detailed statistics, and conclusions have been saved to C:/Users/凡曲/AB_Test_Results/ for further reference.
