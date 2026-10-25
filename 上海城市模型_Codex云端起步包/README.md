# 上海市城市模型 — Codex Cloud 起步仓库

此包不是成品模型，而是可直接放进 GitHub 仓库的**项目起步文件**。

## 1. 使用方法

1. 新建私人 GitHub 仓库（例如 `shanghai-city-model`），将本压缩包内的 `data/`, `AGENTS.md`, `README.md`, `CODEX_PROMPT.txt` 上传到仓库根目录并提交。
2. 在 Codex 桌面应用或网页中新建 `Work in > Cloud` 环境，连接该仓库。
3. 允许对需要的数据域进行访问，并让环境安装所需的 Python 包及可选的无界面 Blender。完成测试后发布环境。
4. 启动一个云任务，将 `CODEX_PROMPT.txt` 全文复制到 Codex 云端任务对话框。
5. 若你已有 building_height、roads、landuse 等 GIS 文件，也上传到 `data/inputs/`；这些数据未包含在此包中。

## 2. 数据与限制

- `data/boundary.csv`: 用户原始五点闭合坐标文件。
- `data/boundary.geojson`: 由 CSV 逐点生成的边界面（不是额外下载的数据）。
- 未经确认，假设经纬度采用 WGS84/EPSG:4326。一定要检查是否混用了 GCJ-02 / BD-09。
- 四角海拔值不是数字高程模型，不应据此虚构地形。
- 没有购买建筑数据或高度 API 的必要；真实覆盖率与真实性取决于开放数据和你已有的 GIS 资料。
- 所有输出文件应由 Codex 真正执行代码生成，不能把本起步包当成已经完成的模型。
