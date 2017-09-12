# Udacity FSWD News Log Analysis Project

## Requirements:
This project requires the following:
* [postgresql](https://www.postgresql.org)
* [python3](https://www.python.org/download/releases/3.0)
* [psycopg2](http://initd.org/psycopg)

## Usage:

1) Install all dependencies.

2) Create a database from the file 'newsdata.sql' and give it a name, like so:

	```psql -f newsdata.sql newsdata```

3) Run the reporting tool

	```python3 generateReport.py```

You will be prompted for the database name. Leave blank to use the default name, 'newsdata'.

## Output:

```
Enter database name to connect to (default is 'newsdata'): newsdata
Connected to 'newsdata'. Generating reports...

Top 3 articles of all time:
1. "Candidate is jerk, alleges rival" - 342,102 views
2. "Bears love berries, alleges bear" - 256,365 views
3. "Bad things gone, say good people" - 171,762 views

Top authors of all time:
1. Ursula La Multa - 512,805 views
2. Rudolf von Treppenwitz - 427,781 views
3. Anonymous Contributor - 171,762 views
4. Markoff Chaney - 85,387 views

Days with greater than 1 percent error rate:
July 17, 2016 - 2.28% errors
```

## Program Design:
This program uses views to make the query logic behind reports easy to read and understand.
The program first creates these views, then generates reports using them.
### Main program logic:
```
...database connection logic...
createViews
	createAuthorArticleView
    createAuthorArticlePopularityView
    createDailyTrafficView
    createDailyErrorView
printReports
	printTopThreeArticles
    printTopAuthors
    printDaysWithErrors
```
### **createViews**
Create views to use in subsequent queries.
#### createAuthorArticleView
Creates author / article view using a LEFT JOIN on the authors and articles table:
```
CREATE TEMPORARY VIEW author_article_view AS
SELECT authors.name AS author,
       articles.slug AS slug,
       articles.title AS title
FROM articles LEFT JOIN authors
ON articles.author=authors.id;
```
#### createAuthorArticlePopularityView
Creates an author / article popularity view using a LEFT JOIN on the previously created author_article_view and log table:
```
CREATE TEMPORARY VIEW author_article_popularity_view AS
  SELECT COUNT(log.path) AS views,
         author_article_view.title AS article,
         author_article_view.author AS author
  FROM author_article_view LEFT JOIN log
  ON log.path LIKE '%' || author_article_view.slug || '%'
  GROUP BY article, author
  ORDER BY views DESC;
```
#### createDailyTrafficView
Creates a daily traffic view from the log table.
```
CREATE TEMPORARY VIEW daily_traffic_view AS
SELECT DATE(time) AS day,
       COUNT(date(time)) AS views
FROM log
GROUP BY day;
```
#### createDailyErrorView
Creates a daily error view from a JOIN of log and daily_traffic_view:
```
CREATE TEMPORARY VIEW daily_error_view AS
SELECT COUNT(status) AS errors,
       DATE(time) AS day
FROM log LEFT JOIN daily_traffic_view
ON date(log.time)=daily_traffic_view.day
WHERE status LIKE '4%'
OR status LIKE '5%'
GROUP BY DATE(time);
```

### **printReports**
Print reports generated from queries.
#### printTopThreeArticles
Simple SELECT with LIMIT on author_article_view:
```
SELECT author_article_popularity_view.article,
       author_article_popularity_view.views
FROM author_article_popularity_view
LIMIT 3;
```
#### printTopAuthors
SELECT using SUM, GROUP BY, ORDER BY on author_article_popularity_view:
```
SELECT author_article_popularity_view.author,
       SUM(author_article_popularity_view.views) AS total_views
FROM author_article_popularity_view
GROUP BY author_article_popularity_view.author
ORDER BY total_views DESC;
```
#### printDaysWithErrors
SELECT using subquery and SQL mathematical functions on daily_error_view, daily_traffic_view views:
```
SELECT * FROM
        (SELECT daily_error_view.day,
               (daily_error_view.errors * 100.0)
                /
               (daily_traffic_view.views * 100.0)
               AS error_rate
         FROM daily_error_view JOIN daily_traffic_view
         ON daily_error_view.day = daily_traffic_view.day)
         AS daily_error_rate
WHERE daily_error_rate.error_rate > 0.01;
```
