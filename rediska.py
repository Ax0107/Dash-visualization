import redis
from ast import literal_eval
import settings

class Rediska(object):
    def parse_data(self, data, lenn):
        """
        Парсит словарь из строки bytes
        :param data: bytes-string-dict
        :param lenn: длинна dict
        :return: dict
        """
        parsed_data = []
        for i in range(0, lenn):
            o = str(data[i])[2:-1]
            parsed_data.append(literal_eval(o))
        return parsed_data

    def get_all_params(self):
        return self.data[0].keys()

    def count_of_objects(self):
        return len(list(set(self.get_from_param('TrackNumber'))))

    def get_from_param(self, needed_param):
        result = []
        for item in self.data:
            for key in self.keys:
                if key == needed_param:
                    result.append(item[key])
        return result

    def get_data_for_object(self, object_num, needed_param):
        if object_num == -1:
            return self.get_from_param(needed_param)
        result = []
        for item in self.data:
            if int(item['TrackNumber']) == int(object_num):
                for key in self.keys:
                    if key == needed_param:
                        result.append(item[key])
        return result

    def __init__(self):
        self.client = redis.Redis(host=settings.HOST, port=settings.PORT, db=settings.DB)
        self.r = self.client.scan()[1]
        self.lenn = self.client.llen(self.r[0])
        self.data = self.parse_data(self.client.lrange(self.r[0], 0, -1), self.lenn)
        self.keys = self.data[0].keys()






