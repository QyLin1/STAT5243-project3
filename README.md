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
