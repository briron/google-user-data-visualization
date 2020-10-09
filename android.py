from html import unescape
import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

class AndroidDataHandler:
    def __init__(self, filepath='', fp=None):
        if not fp:
            if not filepath:
                LOCATION_FILEPATH = './data/Android/activity.html'
                filepath = LOCATION_FILEPATH
            fp = open(filepath, 'r', encoding='utf8')
        raw = fp.read()
        self.android_data = self.preprocess(raw)
    
    def __eraseTag(self, item):
        while item.find('<') != -1:
            start = item.find('<')
            end = item.find('>')
            item = item[:start] + item[(end+1):]
        return item

    def __timeToDatetime(self, line):
        [date, time_standard] = line.split(" 오")
        [year, month, day] = date.split(" ")
        if len(month) == 2:
            month = "0" + month
        if len(day) == 2:
            day = "0" + day
        date = year + " " + month + " " + day
        [noon, time, standard] = time_standard.split(" ")
        if noon.find("후") != -1:
            [hour, min, sec] = time.split(":")
            if hour != "12":
                hour = str(int(hour) + 12)
            time = hour + ":" + min + ":" + sec
        else:
            [hour, min, sec] = time.split(":")
            if len(hour) == 1:
                hour = "0" + hour
            if hour == "12":
                hour = "00"
            time = hour + ":" + min + ":" + sec
        date_time = datetime.datetime.strptime(date + " " + time, "%Y. %m. %d. %H:%M:%S")
        return date_time

    def __parseHTML(self, item):
        splited = item.split('<br>')
        application = unescape(self.__eraseTag(splited[0].split("사용한 앱:")[1].strip()))
        time = splited[1].split('</div>')[0].strip()
        date_time = self.__timeToDatetime(time).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
        return [application, date_time]    

    def preprocess(self, raw):
        ITEM_SPLIT_TAG = '<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">'
        raw = raw.split('<body>')[1].split(ITEM_SPLIT_TAG)[1:]
        activity_list = []
        for item in raw:
            if item.find("사용한 앱:") == -1:
                continue
            activity_list.append(self.__parseHTML(item))
        android_data = pd.DataFrame(activity_list,columns=['activity','datetime'])
        return android_data
    
class AndroidService:
    def __init__(self, ah, fl = None):
        self.ah = ah
        FONT_LOCATION = './font/malgun.ttf'
        if fl is not None:
            FONT_LOCATION = fl
        font_name = fm.FontProperties(fname=FONT_LOCATION).get_name()
        plt.rc('font', family=font_name)

    def visualizeTopCountApp(self, count=10):
        activity_count = ah.android_data.activity.value_counts().head(count)
        patches, texts, autotexts = plt.pie(activity_count, labels = activity_count.index, autopct='%1.1f%%', radius = 1.4, startangle = -60)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_size(11)
            autotext.set_fontweight('bold')
        plt.show()
    
if __name__ == "__main__":
    ah = AndroidDataHandler()
    android_service = AndroidService(ah)