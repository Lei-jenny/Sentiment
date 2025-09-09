# AI Hospitality Sentiment Dashboard - Vercel Deployment

## 部署步骤

### 1. 准备数据文件
- 将您的CSV数据文件重命名为 `data.csv`
- 上传到GitHub仓库的根目录（作为静态文件）

### 2. 部署到Vercel

#### 方法1：通过Vercel CLI
```bash
# 安装Vercel CLI
npm i -g vercel

# 登录Vercel
vercel login

# 部署
vercel

# 生产部署
vercel --prod
```

#### 方法2：通过GitHub集成
1. 将代码推送到GitHub仓库
2. 在Vercel控制台连接GitHub仓库
3. 自动部署

### 3. 配置环境变量（可选）
在Vercel控制台设置以下环境变量：
- `FLASK_ENV=production`
- `FLASK_DEBUG=False`

## 文件结构
```
vercel_deployment/
├── app.py                              # 主应用文件
├── vercel.json                         # Vercel配置
├── requirements.txt                    # Python依赖
├── ai_hospitality_sentiment_dashboard.html  # 前端页面
└── README.md                          # 说明文档
```

## 数据文件
- 将您的CSV文件重命名为 `data.csv`
- 上传到GitHub仓库根目录
- 应用会自动从 `data.csv` 加载数据

## 访问地址
部署成功后，您会获得一个Vercel域名，格式如：
`https://your-app-name.vercel.app`

## 注意事项
1. Vercel免费版有执行时间限制（10秒）
2. 如果数据文件很大，可能需要升级到付费版
3. 建议将数据文件压缩或优化
4. 确保CSV文件编码为UTF-8

## 故障排除
- 如果部署失败，检查 `requirements.txt` 中的依赖版本
- 如果数据加载失败，检查CSV文件格式和编码
- 查看Vercel控制台的部署日志
