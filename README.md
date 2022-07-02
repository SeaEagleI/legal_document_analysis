# 文书网数据挖掘与分析

抓取裁判文书网部分文书，并进行特征分析和罪名预测

## 数据爬取
- 目前爬取了2989757条文书正文数据，json文件大小约21.5G（截至2022-06-01 00:00）
- 最新代码和数据都在服务器上
- 字段解析报告：https://a0o09b6l6h.feishu.cn/docs/doccntph0MBUMJCqN4odgof45kd

## 数据预处理
- 通过编写数据库接口，已经实现了本地低内存条件下的高效数据访问
- judge.db文件大小22G，位于data目录下，支持sqlite3接口访问

## 分析和挖掘
- 表层特征统计（基本，主要使用pandas和sql语句）
- 刑事案件罪名预测

## 参考
- https://github.com/yeyeye777/wenshu_spider (api网址)
- https://gitee.com/Lyong9102/cp_wenshu (模拟生成cookie、逆向js)
- https://blog.csdn.net/feilong_86/article/details/102620316 (逆向js)
- https://blog.csdn.net/weixin_47345503/article/details/118554613 (逆向js)
- https://www.whcsrl.com/blog/1017807 (query分流)
- https://github.com/SeaEagleI/house_price_analysis (多进程并行)
- https://github.com/thunlp/attribute_charge (罪名预测)
