# ⚡ 快速开始指南

## 5分钟快速部署

### Windows用户

1. **双击运行** `run.bat`
   - 系统会自动安装依赖
   - 自动初始化数据库
   - 自动打开浏览器

2. **访问系统**
   ```
   http://localhost:8501
   ```

3. **上传第一份数据**
   - 点击"📤 数据上传"
   - 上传北森导出的两个Excel文件
   - 点击"开始处理数据"

### macOS/Linux用户

1. **终端运行**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

2. **访问系统**
   ```
   http://localhost:8501
   ```

3. **上传数据**（同Windows）

## 📂 文件说明

```
performance_system/
├── app.py                  # 主程序（不要修改）
├── database.py            # 数据库（不要修改）
├── data_processor.py      # 数据处理（不要修改）
├── visualizations.py      # 可视化（不要修改）
├── requirements.txt       # 依赖包（不要修改）
├── run.sh                 # Linux/Mac启动脚本
├── run.bat                # Windows启动脚本
├── view_data.py           # 数据查看工具
├── performance_data.db    # 数据库文件（可备份）
└── README.md             # 完整说明文档
```

## 💡 使用建议

### 首次使用
1. 先上传1-2个月的数据测试
2. 熟悉各个功能页面
3. 确认数据显示正确后再批量导入

### 日常使用
1. 每月从北森导出数据
2. 上传到系统
3. 生成部门报告
4. 监控面谈完成情况

### 数据备份
- 定期备份 `performance_data.db` 文件
- 建议每月备份一次
- 可上传到云盘

## 🆘 遇到问题？

### 常见问题快速解决

**Q: 启动失败？**
```bash
# 检查Python版本
python --version  # 需要 3.8+

# 手动安装依赖
pip install streamlit pandas openpyxl plotly
```

**Q: 上传失败？**
- 检查Excel文件是否来自北森系统
- 确认文件格式正确（.xlsx）
- 查看错误提示信息

**Q: 数据显示异常？**
```bash
# 查看数据库内容
python view_data.py

# 重置数据库（慎用！）
rm performance_data.db
python database.py
```

**Q: 忘记密码？**
系统无密码，本地运行，直接访问即可。

## 📞 技术支持

如需帮助，请查看完整的 `README.md` 文档。

---

**系统版本**: v1.0  
**更新日期**: 2026-04-08  
**开发框架**: Streamlit + SQLite + Plotly
