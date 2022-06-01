# 行政文书挖掘与分析

对裁判文书网上所有行政诉讼文件进行抓取和挖掘分析

## 数据爬取
- 目前爬取了2989757条文书正文数据，json文件大小约21.5G（截至2022-06-01 00:00）
- 最新代码和数据都在服务器上
- 字段解析报告：https://a0o09b6l6h.feishu.cn/docs/doccntph0MBUMJCqN4odgof45kd

## 下一步工作
- 数据预处理（讨论是否需要使用数据库）
- 表面特征统计（基本，主要使用pandas）
- 主题词挖掘
- 案件串挖掘
- 对某个特定方向的案例研究（如教育问题、医患纠纷、彩礼纠纷）
- 其他可能的问题

## 参考

### api网址
- https://github.com/yeyeye777/wenshu_spider

### 通过selenium获得cookie
- https://www.whcsrl.com/blog/1017807
- https://gitee.com/Lyong9102/cp_wenshu

### 参数解析及逆向js
- https://blog.csdn.net/feilong_86/article/details/102620316
- https://gitee.com/Lyong9102/cp_wenshu
- https://blog.csdn.net/weixin_47345503/article/details/118554613

### 分流器
- https://www.whcsrl.com/blog/1017807

### 多进程并行
- https://github.com/SeaEagleI/house_price_analysis
