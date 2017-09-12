#! /usr/bin/env python3

import psycopg2


# Create Views #


def createAuthorArticleView():
    """ Creates author / article view """
    query = """
        CREATE TEMPORARY VIEW author_article_view AS
        SELECT authors.name as author,
               articles.slug as slug,
               articles.title as title
        FROM articles LEFT JOIN authors
        ON articles.author=authors.id;
    """
    connection.cursor().execute(query)


def createAuthorArticlePopularityView():
    """ Creates an author / article popularity view """
    query = """
        CREATE TEMPORARY VIEW author_article_popularity_view AS
        SELECT COUNT(log.path) AS views,
               author_article_view.title AS article,
               author_article_view.author AS author
        FROM author_article_view LEFT JOIN log
        ON log.path LIKE '%' || author_article_view.slug || '%'
        GROUP BY article, author
        ORDER BY views DESC;
    """
    connection.cursor().execute(query)


def createDailyTrafficView():
    """ Creates a daily traffic view """
    query = """
        CREATE TEMPORARY VIEW daily_traffic_view AS
        SELECT DATE(time) as day,
               COUNT(DATE(time)) as views
        FROM log
        GROUP BY day;
    """
    connection.cursor().execute(query)


def createDailyErrorView():
    """ creates a daily error view """
    query = """
        CREATE TEMPORARY VIEW daily_error_view AS
        SELECT COUNT(status) as errors,
               DATE(time) as day
        FROM log LEFT JOIN daily_traffic_view
        ON DATE(log.time)=daily_traffic_view.day
        WHERE status LIKE '4%'
        OR status LIKE '5%'
        GROUP BY DATE(time);
    """
    connection.cursor().execute(query)


def createViews():
    """ CREATE TEMPORARY VIEWs """
    createAuthorArticleView()
    createAuthorArticlePopularityView()
    createDailyTrafficView()
    createDailyErrorView()


# Print Analysis #


def printTopThreeArticles():
    """ Print the top three most popular articles of all time """
    query = """
        SELECT author_article_popularity_view.article,
               author_article_popularity_view.views
        FROM author_article_popularity_view
        LIMIT 3;
    """
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print("\nTop 3 articles of all time: ")
    for i, result in enumerate(results):
        print("{}. \"{}\" - {:,} views".format(i + 1, result[0], result[1]))


def printTopAuthors():
    """ Print the most popular article authors of all time """
    query = """
        SELECT author_article_popularity_view.author,
               SUM(author_article_popularity_view.views) as total_views
        FROM author_article_popularity_view
        GROUP BY author_article_popularity_view.author
        ORDER BY total_views DESC;
    """
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print("\nTop authors of all time: ")
    for i, result in enumerate(results):
        print("{}. {} - {:,} views".format(i + 1, result[0], result[1]))


def printDaysWithErrors():
    """ Print days which had more than 1% of requests lead to errors"""
    cursor = connection.cursor()
    query = """
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
    """
    cursor.execute(query)
    results = cursor.fetchall()
    print("\nDays with greater than 1 percent error rate:")
    for result in results:
        print("{:%B %d, %Y} - {:.2%} errors".format(result[0], result[1]))


def printReports():
    """ Prints all reports """
    printTopThreeArticles()
    printTopAuthors()
    printDaysWithErrors()


# Main #


if __name__ == "__main__":
    # prompt for database name
    prompt = "Enter database name to connect to (default is 'newsdata'): "
    db_name = input(prompt)
    # use default database name if none is given
    if db_name.strip() == "":
        db_name = "newsdata"
    try:
        # attempt to connect to the database
        connection = psycopg2.connect(dbname=db_name)
        print("Connected to '{}'. Generating reports...".format(db_name))
        # create views and print reports
        createViews()
        printReports()
    except psycopg2.Error as e:
        # error when connecting
        print("Unable to connect: \n{}".format(e))
