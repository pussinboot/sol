import os

class IsadoraLoader:
    def __init__(self,total_clipz=0):
        self.clips = []
        self.last_clip_access = total_clipz

    def add_folder(self,folder):
        for item in os.listdir(folder):
            full_path = os.path.join(folder,item)
            if not os.path.isdir(full_path):
                self.clips += [full_path]


    def get_clips(self):
        tor = []
        for i, clip in enumerate(self.clips[self.last_clip_access:]):
            tor += [(clip, str(1 + i + self.last_clip_access))]
        self.last_clip_access = len(self.clips)
        return tor

if __name__ == '__main__':
    test = IsadoraLoader()
    test.add_folder("C:\\VJ\\__clips__\\artsy\\dxv")
    print(test.get_clips())
    test.add_folder("C:\\VJ\\__clips__\\ppl\\dxv")
    print(test.get_clips())
