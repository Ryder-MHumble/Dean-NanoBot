# 信源目录

所有启用信源按维度分组。使用 `source_id` 精确匹配，或 `source_name` 模糊匹配（子串，大小写不敏感）。

---

## national_policy — 国家级政策（6 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `gov_cn_zhengce` | 中国政府网-最新政策 | 国务院政策文件 |
| `ndrc_policy` | 国家发改委-通知公告 | 发改委政策通知 |
| `moe_policy` | 教育部-政策法规 | 教育部政策法规 |
| `most_policy` | 科技部-信息公开 | 科技部政策公开 |
| `samr_news` | 国家市监总局-要闻 | 市场监管总局要闻 |
| `nsfc_news` | 国家自然科学基金委-通知公告 | 基金委项目通知 |

**推荐用法：**
- 查国家政策：`source_names=发改委,教育部,科技部`
- 查基金/科研资助：`source_id=nsfc_news`

---

## beijing_policy — 北京市政策（10 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `beijing_zhengce` | 首都之窗-政策文件 | 北京市政府政策 |
| `bjkw_policy` | 北京市科委/中关村管委会 | 科委 + 中关村政策 |
| `bjjw_policy` | 北京市教委 | 北京教育政策 |
| `bjrsj_policy` | 北京市人社局 | 人力资源社会保障 |
| `ncsti_policy` | 国际科创中心 | 科创中心项目公告 |
| `bjjxj_policy` | 北京市经信局-通知公告 | 经信局工业信息化 |
| `bjzscqj_policy` | 北京市知识产权局-通知公告 | 知识产权相关政策 |
| `bjfgw_policy` | 北京市发改委-政策文件 | 北京发改委政策 |
| `beijing_ywdt` | 首都之窗-要闻 | 北京市要闻动态 |
| `bjrd_renshi` | 北京市人大常委会 | 北京人大人事任免 |

**推荐用法：**
- 查北京教育政策：`source_id=bjjw_policy`
- 查北京科技政策：`source_name=科委`
- 查中关村相关：`source_name=中关村`

---

## personnel — 人事情报（4 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `mohrss_rsrm` | 人社部-国务院人事任免 | 国务院级别任免 |
| `moe_renshi` | 教育部-人事任免 | 教育部官员任免 |
| `cas_renshi` | 中科院-人事任免 | 中科院领导变动 |
| `moe_renshi_si` | 教育部-人事司公告 | 教育部人事司公告 |

**推荐用法：**
- 查国务院人事：`source_id=mohrss_rsrm`
- 查高校/教育系统人事：`source_names=教育部,中科院`

---

## technology — 科技前沿（33 个）

### 国内科技媒体

| source_id | 信源名称 |
|-----------|---------|
| `36kr_ai_rss` | 36氪-AI 频道 |

### 国际科技媒体

| source_id | 信源名称 |
|-----------|---------|
| `techcrunch_ai_rss` | TechCrunch AI |
| `theverge_ai_rss` | The Verge AI |
| `mit_tech_review_rss` | MIT Technology Review |
| `venturebeat_ai_rss` | VentureBeat AI |
| `ieee_spectrum_ai_rss` | IEEE Spectrum AI |
| `wired_ai_rss` | Wired AI |
| `arstechnica_ai_rss` | Ars Technica AI |

### 公司官方博客

| source_id | 信源名称 |
|-----------|---------|
| `openai_blog` | OpenAI Blog |
| `anthropic_blog` | Anthropic News |
| `google_deepmind_blog` | Google DeepMind Blog |
| `meta_ai_blog` | Meta AI Blog |
| `microsoft_ai_blog` | Microsoft AI Blog |
| `mistral_ai_news` | Mistral AI News |
| `stability_ai_news` | Stability AI News |
| `huggingface_blog` | Hugging Face Blog |

### 学术论文

| source_id | 信源名称 |
|-----------|---------|
| `arxiv_cs_ai` | ArXiv cs.AI |
| `arxiv_cs_lg` | ArXiv cs.LG（机器学习） |
| `arxiv_cs_cl` | ArXiv cs.CL（NLP/大模型） |

### 社区讨论

| source_id | 信源名称 |
|-----------|---------|
| `hacker_news` | Hacker News |
| `reddit_ml_rss` | Reddit r/MachineLearning |
| `github_trending` | GitHub Trending |

### 中国 AI 公司

| source_id | 信源名称 |
|-----------|---------|
| `qwen_blog` | Qwen Blog（阿里通义千问） |
| `minimax_news` | MiniMax 新闻动态 |
| `moonshot_research` | 月之暗面-最新研究 |
| `hunyuan_news` | 腾讯混元-最新动态 |

### Twitter/X 监控（需 API Key）

| source_id | 信源名称 | 维度分配 |
|-----------|---------|---------|
| `twitter_ai_kol_international` | Twitter AI KOL（国际） | technology |
| `twitter_ai_kol_chinese` | Twitter AI KOL（华人） | technology |
| `twitter_ai_breakthrough` | Twitter AI 突破性进展 | technology |
| `twitter_ai_papers` | Twitter AI 论文讨论 | technology |
| `twitter_ai_industry` | Twitter AI 产业动态 | industry |
| `twitter_ai_talent` | Twitter AI 人才动态 | talent |

**推荐用法：**
- 查 ArXiv 论文：`source_names=arxiv_cs_ai,arxiv_cs_lg,arxiv_cs_cl`
- 查国际大厂动态：`source_names=OpenAI,DeepMind,Meta AI`
- 查国内大模型：`source_names=通义千问,月之暗面,腾讯混元`
- 查 KOL 观点：使用科技前沿 signals API，`signal_type=kol`

---

## industry — 产业资讯（6 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `36kr_news` | 36氪-快讯 | 科技产业快讯 |
| `tmtpost_news` | 钛媒体 | 深度产业报道 |
| `jiemian_tech` | 界面新闻-科技 | 科技产业新闻 |
| `cyzone_news` | 创业邦 | 创业融资动态 |
| `chinaventure_news` | 投中网 | AI 投融资数据 |

---

## talent — 人才追踪（4 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `semantic_scholar_ai` | Semantic Scholar-AI 论文 | 高引论文 + 学者追踪 |
| `moe_talent` | 教育部人才计划公示 | 长江学者等人才计划 |
| `nature_index` | Nature Index | 高影响力研究机构排名 |
| `wrsa_talent` | 欧美同学会 | 海归人才动态 |

---

## events — 活动日程（4 个）

| source_id | 信源名称 | 说明 |
|-----------|---------|------|
| `aideadlines` | AI Conference Deadlines | 顶会投稿截止日期 |
| `wikicfp` | WikiCFP-AI | AI 相关会议征文 |
| `caai_news` | CAAI 学会新闻 | 中国人工智能学会 |

---

## universities — 高校生态（46+ 个）

### 聚合类（aggregators）

| source_id | 信源名称 |
|-----------|---------|
| `eol_news` | 中国教育在线-要闻 |
| `jyb_news` | 中国教育报 |

### AI 研究机构（ai_institutes）

| source_id | 信源名称 |
|-----------|---------|
| `baai_news` | 北京智源研究院（BAAI） |
| `tsinghua_air` | 清华 AIR（智能产业研究院） |
| `shlab_news` | 上海人工智能实验室 |
| `pcl_news` | 鹏城实验室 |
| `ia_cas_news` | 中科院自动化所 |
| `ict_cas_news` | 中科院计算所 |
| `iie_cas_news` | 中科院信工所 |
| `sii_news` | 上海创智学院 |
| `slai_news` | 深圳河套学院 |

### 奖励与科技（awards）

| source_id | 信源名称 |
|-----------|---------|
| `cas_news` | 中国科学院 |
| `cae_news` | 中国工程院 |
| `nosta_news` | 国家科技奖励办 |
| `moe_keji` | 教育部科学技术与信息化司 |

### 高校新闻（university_news，25 个）

| source_id | 信源名称 |
|-----------|---------|
| `tsinghua_news` | 清华大学新闻网 |
| `pku_news` | 北京大学新闻网 |
| `ustc_news` | 中国科技大学新闻网 |
| `sjtu_news` | 上海交通大学新闻网 |
| `fudan_news` | 复旦大学新闻网 |
| `buaa_news` | 北京航空航天大学新闻网 |
| `bit_news` | 北京理工大学新闻网 |
| `bnu_news` | 北京师范大学新闻网 |
| `ruc_news` | 中国人民大学新闻网 |
| `tju_news` | 天津大学新闻网 |
| `tongji_news` | 同济大学新闻网 |
| `jlu_news` | 吉林大学新闻网 |
| `hit_news` | 哈尔滨工业大学新闻网 |
| `seu_news` | 东南大学新闻网 |
| `xmu_news` | 厦门大学新闻网 |
| `sdu_news` | 山东大学新闻网 |
| `whu_news` | 武汉大学新闻网 |
| `hust_news` | 华中科技大学新闻网 |
| `csu_news` | 中南大学新闻网 |
| `xidian_news` | 西安电子科技大学新闻网 |
| `xjtu_news` | 西安交通大学新闻网 |
| `uestc_news` | 电子科技大学新闻网 |
| `nudt_news` | 国防科技大学 |
| `sysu_news` | 中山大学新闻网 |
| `sustech_news` | 南方科技大学新闻网 |

### 省级教育部门（provincial）

| source_id | 信源名称 |
|-----------|---------|
| `beijing_jw` | 北京市教委 |
| `shanghai_jw` | 上海市教委 |
| `zhejiang_jyt` | 浙江省教育厅 |
| `jiangsu_jyt` | 江苏省教育厅 |
| `guangdong_jyt` | 广东省教育厅 |

**推荐用法：**
- 查清华北大动态：`source_names=清华大学,北京大学`
- 查 AI 研究机构：`group=ai_institutes`（university feed 参数）
- 查两院评选：`source_names=中国科学院,中国工程院`
