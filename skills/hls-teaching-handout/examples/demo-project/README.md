# 可运行示例

在 Skill 根目录执行：

```powershell
python scripts/prepare_preview.py --project "D:\temp\hls-handout-demo" --html "examples\demo-project\editable-handout.html"
python scripts/preview_server.py --project "D:\temp\hls-handout-demo"
```

打开 `http://127.0.0.1:8765`，修改封面、标题、正文和表格单元格，再点击“确认并生成 PDF”。

需要只检查编辑批准流程时，第二条命令加入 `--approval-only`。
