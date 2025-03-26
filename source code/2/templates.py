# templates.py
TEMPLATES = {
    1: {
        'default': '''
        <div class="latest-article">
            <a class="latest-img" href="{url}">
                <span>{category}</span>
                <img src="{img_src}" loading="lazy" alt="{title}" width="500" height="250" />
            </a>
            <div class="lastest-title-box">
                <h3><a href="{url}">{title}</a></h3>
                <time datetime="{datetime}" pubdate="pubdate">{date}</time>
                <p>{description}</p>
            </div>
        </div>
        '''
    },
    2: {
        'default': '''
        <div class="recent_post">
            <a class="recent_img" href="{url}">
                <img loading="lazy" src="{img_src}" alt="{title}" />
            </a>
            <div class="recent_right">
                <h3><a href="{url}">{title}</a></h3>
                <time datetime="{datetime}" pubdate="pubdate">{date}</time>
            </div>
        </div>
        '''
    },
    3: {
        'default': '''
        <div class="relate_article">
            <a href="{url}"><img src="{img_src}" loading="lazy" alt="{title}" /></a>
            <h3><a title="{title}" href="{url}">{title}</a></h3>
        </div>
        '''
    },
    4: {
        'default': '''
        <div class="black_a"><a class="black_img" href="{url}"><img src="{img_src}" loading="lazy" alt="{title}" /></a>
        <div class="black_right">
            <h3> <a title="{title}" href="{url}">{title}</a></h3>
            <p>by Achilles.H</p>
        </div>
        </div>
        '''
    },
    5: {
        'default': '''
        <a class="article-div" href="{url}">
            <h5 class="title-h5">{title}</h5>
            <time class="time" datetime="{datetime}" pubdate="pubdate">{date}</time>
            <p class="resume">{description}</p>
        </a>
        '''
    },
    6: {
        'with_description': '''
        <div class="article item-{item_number}"> <a class="pro_img" href="{url}"><img src="{img_src}" alt="{title}" /></a>
            <div class="article_content"> <span>{category}</span>
                <h2><a class="title-h2" title="{title}" href="{url}">{title}</a></h2>
                <p>{description}</p>
            </div>
        </div>
        ''',
        'without_description': '''
        <div class="article item-{item_number}"> <a class="pro_img" href="{url}"><img src="{img_src}" alt="{title}" /></a>
            <div class="article_content"> <span>{category}</span>
                <h2><a class="title-h2" title="{title}" href="{url}">{title}</a></h2>
            </div>
        </div>
        '''
    }
}
