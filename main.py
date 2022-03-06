import os
from urllib import parse
import json
import requests
from time import sleep

# шкала размеров VK API
size_scale = {'w': 6, 'z': 5, 'y': 4, 'x': 3, 'm': 2, 's': 1, 'o': 0, 'p': 0, 'q': 0, 'r': 0}


class VkUser:
    def __init__(self, name, vk_token):
        self.name = name
        self.token = vk_token

    def get_id(self):
        print('Получаем id пользователя')
        url = 'https://api.vk.com/method/users.get?v=5.131'
        url += '&access_token=' + self.token + '&user_ids=' + self.name
        response = requests.get(url).json()['response'][0]
        self.id = response['id']


class VKFoto:
    def __init__(self,size, like_quant, date, height, width, pic_url):
        self.size = size
        self.like_quant = like_quant
        self.date = date
        self.height = height
        self.width = width
        self.pic_url = pic_url

    def __lt__(self, other):
        if not isinstance(other, VKFoto):
            print("Error")
        else:
            if (self.width * self.height) < (other.width * other.height):
                return True
            else:
                if (self.width * self.height) > (other.width * other.height):
                    return False
                else:
                    # считаем, что при одинаковой площади меньше периметр - лучше соотношение сторон
                    return (self.width + self.height) > (other.width + other.height)


class YaUploader:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def make_dir(self, folder):
        print('Создаем папку')
        url = 'https://cloud-api.yandex.net/v1/disk/resources?'
        url += 'path=' + str(folder)
        headers = self.get_headers()
        response = requests.put(url, headers=headers)
        return response.status_code

    def upload(self, reesrt, folder):
        self.make_dir(folder)
        print('Загружаем картинки на диск')
        for picture in reesrt:
            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload?'
            params = {'path': str(folder + '/' + picture.name + '.jpg'), 'url': picture.pic_url}
            url += parse.urlencode(params)
            headers = self.get_headers()
            requests.post(url, headers=headers)
            sleep(0.23)


def make_pict_names(reestr):
    print("Создаем уникальные имена картинкам")
    name_list = []
    for picture in reestr:
        if picture.like_quant in name_list:
            picture.name = str(picture.like_quiant) + str(picture.date)
        else:
            picture.name = str(picture.like_quant)
            name_list.append(picture.like_quant)


def get_pics(user: VkUser, pic_quant):
    print('Выбираем фотографии')
    offset = 0
    reestr = []
    while True:
        url = 'https://api.vk.com/method/photos.get?v=5.131&extended=1&album_id=profile&count=100'
        url += '&access_token=' + user.token
        url += '&owner_id=' + str(user.id)
        url += '&offset=' + str(offset)
        response = requests.get(url).json()
        if not response['response']['items']:
            make_pict_names(reestr)
            return reestr
        for item in response['response']['items']:
            max_size = 'r'
            max_height = 0
            max_width = 0
            pic_url = ''
            for size in item['sizes']:
                if size_scale[size['type']] > size_scale[max_size]:
                    max_size = size['type']
                    max_height = size['height']
                    max_width = size['width']
                    pic_url = size['url']
            reestr.append(VKFoto(max_size, item['likes']['count'], item['date'], max_height, max_width, pic_url))
            if len(reestr) > pic_quant:
                reestr.sort(reverse=True)
                reestr.pop()
        sleep(0.33)
        offset += 100


def get_tokens(file_name):
    with open(file_name, 'r') as f:
        tokens = json.load(f)
    return tokens


if __name__ == '__main__':
    tokens = get_tokens('tokens')
    user = VkUser(input('Введите id или ник пользователя ВК: '), tokens['VK'])
    pic_quant = int(input('Какое количество фотографий сохранить? ') or 5)
    user.get_id()
    reestr = get_pics(user, pic_quant)
    uploader = YaUploader(tokens['YA'])
    uploader.upload(reestr, user.id)
    print('Загрузка завершена')
