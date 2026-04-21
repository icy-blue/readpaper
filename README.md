# Translate Paper Forest

本仓库用于把 `translate.icydev.cn` 上的论文内容整理成一个本地研究知识森林，并生成可浏览的 Markdown / HTML 阅读站点。

## 目录约定

- `outputs/papers/`: 归一化后的单篇论文 JSON
- `outputs/raw/`: 从 translate 服务抓取的原始 payload
- `outputs/site/`: 生成后的站点资源
- `scripts/`: 归一化、邻居回填、站点渲染等脚本
- `references/`: schema 与输出约定

## 重跑网站

当你更新了论文记录、论文邻居，或者前端代码后，按下面顺序重跑站点：

```bash
python3 scripts/normalize_papers.py \
  --raw-dir outputs/raw \
  --papers-dir outputs/papers

python3 scripts/backfill_paper_neighbors.py \
  --papers-dir outputs/papers

python3 scripts/render_markdown_site.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site

npm run build:web

python3 scripts/render_html_dashboard.py \
  --neighbors-json outputs/site/paper-neighbors.json \
  --output outputs/site/index.html
```

各步骤作用：

- `normalize_papers.py`: 从 `outputs/raw/` 重新生成 `outputs/papers/` 的标准化论文记录
- `backfill_paper_neighbors.py`: 重新计算每篇论文的任务 / 方法 / 对比近邻
- `render_markdown_site.py`: 生成站点需要的 Markdown 页面和 `paper-neighbors.json`
- `npm run build:web`: 重新构建前端静态资源
- `render_html_dashboard.py`: 把最新 `paper-neighbors.json` 和前端构建产物发布到 `outputs/site/index.html`

## 常规工作流

如果需要从源站抓取新论文，可先执行：

```bash
python3 scripts/fetch_translate_papers.py \
  --registry state/paper_registry.json \
  --manifest outputs/fetch/latest-fetch.json \
  --raw-dir outputs/raw \
  --limit 20
```

之后可继续执行：

```bash
python3 scripts/build_registry.py \
  --papers-dir outputs/papers \
  --registry state/paper_registry.json
```

## 注意事项

- 把 `translate.icydev.cn` 视为只读数据源
- 默认从仓库根目录运行脚本
- 不要手改 `outputs/site/` 下的生成结果，除非是在调试渲染流程
- 如果修改了 schema 或输出结构，请同步更新 `references/` 中的约定文档
