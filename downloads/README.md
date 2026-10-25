# 上海城市模型成果下载

[下载最新第三版 ZIP（约 41.6 MB）](./shanghai-city-model-delivery-v3.zip?raw=true)

[下载历史第二版 ZIP（约 13.2 MB）](./shanghai-city-model-delivery-v2.zip?raw=true)

如果 GitHub 文件页面不直接下载，请点击文件页面的 **Download raw file**。私人仓库需要先登录有访问权限的 GitHub 账号。

成果包含 GeoPackage、全域/分层/28个瓦片 GLB、可编辑 Blender 工程、四张 PNG、自动化脚本、原始 OSM 缓存和质量报告。解压后先阅读 `outputs/使用说明.md`、`outputs/更新记录.md` 和 `outputs/reports/QA.md`。完整性校验见本目录 `SHA256SUMS.txt`。

边界面积约22.0091平方公里；第三版有11856个地上建筑体块、1597条道路中心线及道路面、映射河渠面段和19个树点。通过Overture 2026-10-21.0核查，接纳10123条东亚建筑源记录，裁切后形成10125个补充面片；146个高冲突候选留待复核。修复旧解析规则漏掉的一条约500米闭合跑步通道。35个GLB和含12425个网格对象的Blender工程已实际读回验证，压缩包所有文件SHA-256已核对。

这是有来源依据的模型，现实完整性仍未经独立现状清单验证。新增轮廓的上游版本标记2024-11-01，影像采集日期未核实，可能存在拆建变化。建筑高度全部为明确标记的估计，新增建筑按用地上下文采用6/8/12/15米低置信度默认值；部分道路/河渠宽度和树冠尺寸也为估计。桥隧高程为示意，其中9段示意坡度异常已列入QA，不能作为实测纵坡。没有DEM，基底不是实测地形。未在SketchUp 2025中进行原生导入测试。

© OpenStreetMap contributors；Overture Maps Foundation；East Asian Buildings doi:10.5281/zenodo.8174931。官方Overture建筑/交通集合声明ODbL-1.0，源和派生数据库分享时保留署名并履行相应许可义务。ESA WorldCover参考资料为CC-BY-4.0。微软官方索引不覆盖本研究区；Overture建筑已核查合并，道路与水体因同源OSM不冒充独立补充。逐来源版本、许可字段、原始几何及接纳/排除决策均在成果包中。
