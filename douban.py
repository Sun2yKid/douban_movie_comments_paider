from urllib import request
import re
import pandas as pd
import numpy
from os import path

from bs4 import BeautifulSoup as bs
import jieba
from wordcloud import WordCloud

d = path.dirname(__file__)
font = r'C:\Windows\Fonts\simfang.ttf'
nowplaying_list = []

def get_nowplaying_list():
    resp = request.urlopen('https://movie.douban.com/cinema/nowplaying/beijing/')
    html_data = resp.read().decode('utf-8')
    # with open("douban_movie.html", "w", encoding='utf-8') as my_file:
    #   my_file.write(html_data)

    soup = bs(html_data, "html.parser")
    # print(soup.prettify())
    nowplaying_movies = soup.find_all('div', id='nowplaying')
    nowplaying_movies_list = nowplaying_movies[0].find_all('li', class_='list-item')
    counter = 0
    for movie in nowplaying_movies_list:
        nowplaying_dict = {}
        counter += 1
        nowplaying_dict['id'] = movie['data-subject']
        nowplaying_dict['director'] = movie['data-director']
        nowplaying_dict['title'] = movie['data-title']
        for movie_img in movie.find_all('img'):
            nowplaying_dict['img'] = movie_img['src']
        # nowplaying_dict['img'] = movie.find_all('img')[0]['src']
        nowplaying_list.append(nowplaying_dict)
        print(str(counter) + ':' + nowplaying_dict['title'])

    with open("douban_nowplaying_movie.txt", "w", encoding='utf-8') as my_file:
        my_file.write(str(nowplaying_list))

def get_comments(movie_id):
    movie_comments_url = 'https://movie.douban.com/subject/' + nowplaying_list[movie_id-1]['id'] + '/comments?start=0'
    resp = request.urlopen(movie_comments_url)
    html_data = resp.read().decode('utf-8')
    soup = bs(html_data, "html.parser")
    current_page_comments = soup.find_all('div', class_='comment')
    comments_list = []
    for comment in current_page_comments:
##        print(comment.p.find_all(text=True, recursive=False))
##        print(type(comment.find_all('p')))
##        comments_list.append(comment.find_all('p')[0].string)
        comments_list.append(comment.p.find_all(text=True, recursive=False)[0].string)
        with open("movie_comments.txt", "w", encoding='utf-8') as my_file:
            my_file.write(str(comments_list))

    comments = ''
    for k in range(len(comments_list)):
        comments += (str(comments_list[k]))
    return comments

def handle_comments(comments_string):
    # 取出中文
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    filterdata = re.findall(pattern, comments_string)
    cleaned_comments = ''.join(filterdata)
    
    # 中文分词
    segment = jieba.lcut(cleaned_comments)
    
    # 剔除停用词统计
    words_df=pd.DataFrame({'segment':segment})
    stopwords=pd.read_csv("stopwords.txt",index_col=False,quoting=3,sep="\t",names=['stopword'], encoding='utf-8')#quoting=3全不引用
    words_df=words_df[~words_df.segment.isin(stopwords.stopword)]
    words_stat = words_df.groupby(by=['segment'])['segment'].agg({"计数":numpy.size})
    words_stat = words_stat.reset_index().sort_values(by=["计数"], ascending=False)
    
    wordcloud=WordCloud(font_path=font, background_color="white",max_font_size=80) #指定字体类型、字体大小和字体颜色
    word_frequence = {x[0]:x[1] for x in words_stat.head(1000).values}
    word_frequence_list = []
    for key in word_frequence:
        temp = (key,word_frequence[key])
        word_frequence_list.append(temp)
     
    wordcloud=wordcloud.fit_words(dict(word_frequence_list))
    return wordcloud
    
    
# 创建停用词list
def stopwordslist(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]
    return stopwords

# 对句子进行分词
def seg_sentence(sentence):
    sentence_seged = jieba.cut(sentence.strip())
    stopwords = stopwordslist(path.join(d, 'stopwords.txt'))
    outstr = ''
    for word in sentence_seged:
        if word not in stopwords:
            if word != '\t':
                outstr += word
                outstr += " "
    return outstr

def handle_comments2(comments_string):
    # 取出中文
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    filterdata = re.findall(pattern, comments_string)
    cleaned_comments = ''.join(filterdata)
    text = seg_sentence(cleaned_comments)
    wordcloud = WordCloud(collocations=False, font_path=font, width=1400, height=1400, margin=2).generate(text)
    return wordcloud

def generate_cloud(wordcloud):
    import matplotlib.pyplot as plt
    
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.show()
    wordcloud.to_file('show_comments.png')
    
##    plt.imshow(wordcloud, interpolation='bilinear')
##    plt.axis("off")
##
##    wordcloud = WordCloud(max_font_size=40).generate(text)
##    plt.figure()
##    plt.imshow(wordcloud, interpolation='bilinera')
##    plt.axis("off")
##    plt.show()

##    image = wordcloud.to_image()
##    image.show()
##    image.to_file('show_comments.png')

def main():
    print("""
        #########我是爬虫---妖小爬########
        爬一爬豆瓣上最近上映的电影
        ##################################
        """)
    get_nowplaying_list()
    print("爬完了...")
    index = None
    index = input("请输入你希望查询的电影编号：")
    while not index:
        index = input("请输入你希望查询的电影编号：")
        print("输入为空，请重新输入")
    print('ok:', index, '查询中')
    wordcloud = handle_comments2(get_comments(int(index)))
    generate_cloud(wordcloud)


if __name__ == '__main__':
    main()
