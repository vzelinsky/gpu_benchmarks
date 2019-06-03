from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
from ast import literal_eval


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


def get_gpu_data():
    raw_html = simple_get("https://www.videocardbenchmark.net/gpu_list.php")
    soup = BeautifulSoup(raw_html, 'html.parser')
    table_rows = soup.find("table", {"id" : "cputable"}).find("tbody").find_all("tr")
    all_gpus = []
    for row in table_rows:
        tds = row.find_all("td")
        if(tds[4].text != 'NA'):
            benchmark = re.sub('[^0-9\.]', '', tds[1].text)
            price = re.sub('[^0-9\.]', '', tds[4].text)
            all_gpus.append((tds[0].text, benchmark, price))
    sorted_gpus = sorted(all_gpus, key=lambda x:int(x[1]), reverse=True)
    with open("gpu_benchmark_price.txt", "w", encoding='utf-8') as file:
        for gpu in sorted_gpus:
            file.write(str(gpu) + "\n")


def plot_gpu_data():
    gpus = []
    value_scores = []
    benchmarks = []
    with open("gpu_benchmark_price.txt", "r", encoding="ascii", errors="ignore") as file:
        for line in file:
            gpu = literal_eval(line)
            benchmark = float(gpu[1])
            price = float(gpu[2])
            value_scores.append(benchmark/price)
            benchmarks.append(benchmark)
            gpus.append(gpu)
    fig,ax = plt.subplots()
    sc = plt.scatter(benchmarks, value_scores, cmap=plt.cm.RdYlGn)

    annot = ax.annotate("", xy=(0,0), xytext=(0,20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def update_annot(ind):
        pos = sc.get_offsets()[ind["ind"][0]]
        annot.xy = pos
        text = "{}, {}".format(" ".join(list(map(str,ind["ind"]))), 
                            " ".join([gpus[n][0] for n in ind["ind"]]))
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.4)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = sc.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.show()


if __name__ == "__main__":
    # get_gpu_data()
    plot_gpu_data()
