# 法律文书数据挖掘与分析

抓取裁判文书网部分文书，并进行特征分析和罪名预测

## 数据爬取
- 目前爬取了2989757条文书正文数据，json文件大小约21.5G（截至2022-06-01 00:00）
- 字段列表、含义及值集合：[wenshulist1.js](data/wenshulist1.js)
- 前100个正文数据样本：[sample_100.json](data/sample_100.json)
- 截至2022年6月25日所有1.3亿文书的元数据：[count](data/count)

## 数据预处理
- 通过编写数据库接口，已经实现了本地低内存条件下的高效数据访问
- judge.db文件大小22G，位于服务器的data目录下，支持sqlite3接口访问

## 分析和挖掘
- 表层特征统计（主要使用左菜单栏爬虫）
- 刑事案件罪名预测（数据集的标注格式和预测模型参考刘知远组的COLING18[论文](http://nlp.csai.tsinghua.edu.cn/~tcc/publications/coling2018_attribute.pdf)）

## 参考
- https://github.com/yeyeye777/wenshu_spider (api网址)
- https://gitee.com/Lyong9102/cp_wenshu (模拟生成cookie、逆向js)
- https://blog.csdn.net/feilong_86/article/details/102620316 (逆向js)
- https://blog.csdn.net/weixin_47345503/article/details/118554613 (逆向js)
- https://www.whcsrl.com/blog/1017807 (query分流)
- https://github.com/SeaEagleI/house_price_analysis (多进程并行)
- https://github.com/thunlp/attribute_charge (罪名预测)
