#from pyspark.sql import SparkSession
#from pyspark.sql import *
from pyspark.sql import SparkSession
from pyspark.sql.functions import  udf
from datetime import  datetime
#from pyspark.sql.types import *
spark = SparkSession \
    .builder \
    .appName("details_check") \
    .enableHiveSupport() \
    .getOrCreate()

spark.sql("use aikang")

##创建当月销售数据报表
def saler_report(month):
    sql=""" select a.name,a.team,a.manager
    ,b.{month}month
    ,c.local_cost,c.local_city_num
    ,d.other_city_cost,d.other_city_num 
    ,c.local_cost+d.other_city_cost as total_cost
    ,c.local_city_num+d.other_city_num as total_num 
    ,(c.local_cost+d.other_city_cost)/10000/{month}month as finish_percent
    from working_saler a 
    left join saler_aim b 
    on a.name=b.name
    left join (select saler,sum(cost) as local_cost ,count(*) as local_city_num 
    from details where month(`date`)={month} group by saler) c 
    on a.name=c.saler
    left join (select saler,sum(cost) as other_city_cost,sum(number) as other_city_num 
    from other_city_cost group by saler) d 
    on d.saler =a.name  """.format(month=month)
    return spark.sql(sql)

#创建完销售报表后创建，经理销售报表
def manager_report(dataframe_saler,month):
    dataframe_saler.createOrReplaceTempView("temp")
    sql = """select a.*,m.{month}month,all_cost/m.{month}month as finish_percent 
        from
        (select {group} 
        ,sum(local_cost)
        ,sum(local_city_num)
        ,sum(other_city_cost)
        ,sum(other_city_num)
        ,sum(total_cost) all_cost
        ,sum(total_num) from temp 
        group by {group})a
        left join manager_aim m on m.team=a.{group}""".format(group="manager", month=month)
    return spark.sql(sql)
#团队销售报表
def team_report(dataframe_saler,month):
    dataframe_saler.createOrReplaceTempView("temp")
    sql="""select a.*,m.{month}month,all_cost/m.{month}month as finish_percent 
    from
    (select {group} 
    ,sum(local_cost)
    ,sum(local_city_num)
    ,sum(other_city_cost)
    ,sum(other_city_num)
    ,sum(total_cost) all_cost
    ,sum(total_num) from temp 
    group by {group})a
    left join manager_aim m on m.team=a.{group}""".format(group="team",month=month)
    return spark.sql(sql)


##上传dataframe到指定数据表中，命名格式xxx_month_report,例如saler_11month_report
def upload_to_mysql(dataframe,tablename):
    dataframe.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://localhost:3306/aikang") \
        .option("dbtable",tablename) \
        .option("user", "root") \
        .option("password", "jianwei") \
        .save()


def read_from_mysql(tablename):
    jdbcDF=spark.read\
        .format("jdbc")\
        .option("url", "jdbc:mysql://localhost:3306/aikang") \
        .option("dbtable", tablename) \
        .option("user", "root") \
        .option("password", "jianwei") \
        .load()
    return jdbcDF

##获取11月销售人员,经理，团队报表
saler_11month_report=saler_report(11)
manager_11month_report=manager_report(saler_11month_report,11)
team_11month_report=team_report(saler_11month_report,11)

#将报表传入数据库中
upload_to_mysql(saler_11month_report,"saler_11month_report")
upload_to_mysql(manager_11month_report,"manager_11month_report")
upload_to_mysql(team_11month_report,"team_11month_report")