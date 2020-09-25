from flask import Flask
import datetime
import xlwt
import pymongo

app = Flask(__name__)


@app.route('/')
def hello_world():
    #test()
    return 'hello!'


@app.route('/specific')
def export_specific():
    export_excel()
    return 'Done!'


@app.route('/all')
def export_all():
    export_excel_all()
    return 'Done!'

def test():
    client=pymongo.MongoClient("mongodb://mongo:27017/scrapydata")
    collection = client['scrapydata']['test']
    collection.insert_one({"_id":123,"name":'test'})

def export_excel():
    try:
        client = pymongo.MongoClient('mongodb://mongo:27017/scrapydata')
        db = client['scrapydata']
        collection_words = db['words']
        collection_amz = db['amz']
        today = datetime.datetime.now()
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)
        sheet.write(0, 0, "words")
        sheet.write(0, 1, "ASIN")
        sheet.write(0, 2, "PageIndex")
        sheet.write(0, 3, "CurrentPageRank")
        sheet.write(0, 4, 'TotalRank')
        sheet.write(0, 5, 'IsAd')
        r = 1
        for word in collection_words.find():
            has_result = False
            for amz in collection_amz.find({'SearchWords': word['keys'], "ASIN": word['ASIN']}):
                has_result = True
                sheet.write(r, 0, amz['SearchWords'])
                sheet.write(r, 1, amz['ASIN'])
                sheet.write(r, 2, int(amz['PageIndex']))
                sheet.write(r, 3, int(amz['CurrentPageRank']))
                sheet.write(r, 4, int(amz['TotalRank']))
                sheet.write(r, 5, amz['IsAd'])
            if has_result:
                r += 1
        wbk.save('amz' + str(today.date()) + '.xls')

    except Exception as e:
        print(e)


def export_excel_all():
    try:
        #client = pymongo.MongoClient('mongodb://liurui:rootroot@192.168.15.92:27017/scrapydata')
        client = pymongo.MongoClient('mongodb://mongo:27017/scrapydata')
        db = client['scrapydata']
        collection_amz = db['amz']
        today = datetime.datetime.now()
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)
        sheet.write(0, 0, "words")
        sheet.write(0, 1, "ASIN")
        sheet.write(0, 2, "PageIndex")
        sheet.write(0, 3, "CurrentPageRank")
        sheet.write(0, 4, 'TotalRank')
        sheet.write(0, 5, 'IsAd')
        sheet.write(0, 6, 'RequestUrl')
        r = 1
        for amz in collection_amz.find():
            sheet.write(r, 0, amz['SearchWords'])
            sheet.write(r, 1, amz['ASIN'])
            sheet.write(r, 2, int(amz['PageIndex']))
            sheet.write(r, 3, int(amz['CurrentPageRank']))
            sheet.write(r, 4, int(amz['TotalRank']))
            sheet.write(r, 5, amz['IsAd'])
            sheet.write(r, 6, amz['RequestUrl'])
            r += 1
        wbk.save('amz_all' + str(today.date()) + '.xls')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    app.run()
    #app.run(host="0.0.0.0", debug=True)
