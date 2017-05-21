import os
import time
import sys

from shutil import copyfile

from sol.magi import Magi
from sol.inputs import osc

"""
backend for gui made in vvvv
hosts magi and sends data to an osc_client
"""

from sol.config import GlobalConfig
C = GlobalConfig()


BASE_ADDR = '/modvj/sol_mt/'


class MTGui:
    """
    can be used w/o printing state and since it doesn't control magi
    can be used simulatenously with another gui :^), just make sure to
    wrap all gui update functions to perform both things in that case
    """

    def __init__(self, magi, ip="127.0.0.1", port=6666):
        self.magi = magi
        self.osc_client = osc.OscClient(ip, port)
        self.update_all()

    @property
    def to_copy_dir(self):
        return os.path.join(C.SCROT_DIR, 'TO_COPY')

    def update_all(self):
        self.update_cols('start')
        for i in range(len(self.magi.clip_storage.current_clips)):
            clip = self.magi.clip_storage.current_clips[i]
            if clip is not None:
                self.update_clip(i, clip)

    def update_loop(self, layer, clip):
        # have to send everything as numbers
        # loop on   - off = 0, on = 1
        # loop_type - 'd' = 0, 'b' = 1
        loop_on = 0
        loop_type = 0
        loop_type_lookup = {'d': 0, 'b': 1}
        if clip is not None:
            # loop on
            loop_on = int(clip.params['loop_on'])
            # get the loop
            loop_select = clip.params['loop_selection']
            if loop_select >= 0:
                cur_loop = clip.params['loop_points'][loop_select]
                # loop type
                if cur_loop is not None:
                    loop_type = loop_type_lookup[cur_loop[2]]
        loop_addr = BASE_ADDR + 'layer{}/loop/'.format(layer)
        self.osc_client.build_n_send(loop_addr + 'on_off', loop_on)
        self.osc_client.build_n_send(loop_addr + 'type', loop_type)
        if clip is not None:
            self.update_lp(layer, clip)
            self.update_cur_loop_range(layer, clip)

    def update_cur_loop_range(self, layer, clip):
        cl = self.magi.loop_get(layer)
        loop_addr = BASE_ADDR + 'layer{}/loop/'.format(layer)
        if cl is not None:
            try:
                cur_range = "{:1.4},{:1.4}".format(cl[1][0], cl[1][1])
            except:
                cur_range = "0,1"
            self.osc_client.build_n_send(loop_addr + 'cur_range', cur_range)
        else:
            self.osc_client.build_n_send(loop_addr + 'cur_range', "0,1")

    def update_qp(self, layer, clip):
        qps = clip.params['cue_points']
        qps_str = ",".join(["1" if qp is not None else "0" for qp in qps])
        qp_addr = BASE_ADDR + 'layer{}/qp'.format(layer)
        self.osc_client.build_n_send(qp_addr, qps_str)

    def update_lp(self, layer, clip):
        lps = clip.params['loop_points']
        lps_str = ",".join(["1" if lp is not None else "0" for lp in lps])
        loop_no = clip.params['loop_selection']
        loop_addr = BASE_ADDR + 'layer{}/loop/'.format(layer)
        self.osc_client.build_n_send(loop_addr + 'lp', lps_str)
        self.osc_client.build_n_send(loop_addr + 'lp_i', loop_no)

    def update_speed(self, layer, clip):
        spd = clip.params['playback_speed']
        spd_addr = BASE_ADDR + 'layer{}/spd'.format(layer)
        self.osc_client.build_n_send(spd_addr, spd)

    def update_sens(self, layer, clip):
        sens = clip.params['control_sens']
        sens_addr = BASE_ADDR + 'layer{}/sens'.format(layer)
        self.osc_client.build_n_send(sens_addr, sens)

    def update_cur_clip_sel(self, layer, clip):
        clip_i_addr = BASE_ADDR + 'layer{}/cur_col_clip_i'.format(layer)
        if clip in self.magi.clip_storage.clip_col:
            clip_i = self.magi.clip_storage.clip_col.index(clip)
            # print(self.magi.clip_storage.current_clips.index(clip)) # sanity
            # check
        else:
            clip_i = -1
        self.osc_client.build_n_send(clip_i_addr, clip_i)

    # magi required funs #
    def update_clip(self, layer, clip):
        if clip is None:
            return
        self.update_loop(layer, clip)
        self.update_speed(layer, clip)
        self.update_sens(layer, clip)
        self.update_qp(layer, clip)
        self.update_cur_clip_sel(layer, clip)

    def update_clip_params(self, layer, clip, param):
        param_dispatch = {
            'cue_points': self.update_qp,
            'loop_points': self.update_loop,
            'loop_on': self.update_loop,
            'loop_type': self.update_loop,
            'loop_selection': self.update_loop,
            'playback_speed': self.update_speed,
            'control_sens': self.update_sens
        }
        if param not in param_dispatch:
            return
        param_dispatch[param](layer, clip)

    def update_cur_pos(self, layer, pos):
        pos_addr = BASE_ADDR + 'layer{}/cur_pos'.format(layer)
        self.osc_client.build_n_send(pos_addr, pos)

    def update_search(self):
        pass

    def update_cols(self, what, ij=None):
        # print('updating cols',what)
        # clip_thumbs
        thumbs_to_send = []
        for i in range(len(self.magi.clip_storage.clip_col.clips)):
            cur_col_clip = self.magi.clip_storage.clip_col.clips[i]
            if cur_col_clip is None or cur_col_clip.t_names is None:
                thumbs_to_send += ["None"]
            else:
                t_name = cur_col_clip.t_names[0]
                fname = os.path.split(t_name)[1][::-1]
                first_part = fname[fname.find("_") + 1:]
                thumb_no = first_part[:first_part.find("_")][::-1]
                thumbs_to_send += [thumb_no]
        to_send = ','.join(thumbs_to_send)
        self.osc_client.build_n_send(BASE_ADDR + 'update_thumbs', to_send)
        for i in range(len(self.magi.clip_storage.current_clips)):
            self.update_cur_clip_sel(
                i, self.magi.clip_storage.current_clips[i])

    def update_clip_names(self):
        pass

    # file operations
    def gen_thumbs_for_me(self):
        # makes sure all thumbnail hashes are unique and renames equivalent
        # thumbs

        def change_hash(clip, old_hash, new_hash):
            # clip.t_names
            to_move = clip.t_names
            clip.t_names = [t_name.replace(
                old_hash, new_hash, 1) for t_name in clip.t_names]
            new_names = [t_name for t_name in clip.t_names]
            for i, lp in enumerate(clip.params['loop_points']):
                if lp is not None:
                    if lp[3] is not None:
                        to_move += [lp[3]]
                        new_names += [lp[3].replace(old_hash, new_hash, 1)]
                        clip.params['loop_points'][i][3] = new_names[-1]
            for i in range(len(to_move)):
                try:
                    os.rename(to_move[i], new_names[i])
                except:
                    pass

        def copy_file(src_file, new_hash):
            # src_file = clip.t_names[0]
            new_file = os.path.join(
                self.to_copy_dir, '{}.png'.format(new_hash))
            try:
                copyfile(src_file, new_file)
            except:
                pass

        if not os.path.exists(self.to_copy_dir):
            os.makedirs(self.to_copy_dir)
        thumbz = {}
        for clip in self.magi.db.clips.values():
            test_str = clip.t_names[0]
            fname = os.path.split(test_str)[1][::-1]
            first_part = fname[fname.find("_") + 1:]
            thumb_no = first_part[:first_part.find("_")][::-1]
            try:
                int(thumb_no)
            except:
                print(thumb_no, 'not a number', '\n\t', test_str)
            if thumb_no in thumbz:
                print('not unique', thumb_no)
                # print(os.path.split(test_str)[0] + '_to_move/' + thumb_no + '.png')
                fix_hash = int(thumb_no)
                counter = 0
                while str(fix_hash) in thumbz:
                    fix_hash += 1
                    counter += 1
                fix_hash = str(fix_hash)
                print('now unique {} (+{})'.format(fix_hash, counter))
                change_hash(clip, thumb_no, fix_hash)
                thumbz[thumb_no] = test_str
            else:
                thumbz[thumb_no] = test_str
            copy_file(test_str, thumb_no)
        print('done copying your thumbnails, find them at')
        print(self.to_copy_dir)

    def print_current_state(self):
        to_print = "*-" * 36 + "*\n" + \
            self.print_cur_clip_info() + "\n" + \
            self.print_a_line() + "\n" + \
            self.print_cur_col() + \
            self.print_a_line() + "\n" + \
            self.print_cols()

        print(to_print)

    def print_cur_clip_info(self):
        name_line = []
        pb_line = []
        pos_line = []
        spd_line = []
        sens_line = []
        loop_line_0 = []
        loop_line_1 = []
        qp_line_0 = []
        qp_line_1 = []
        loop_type_lookup = {'b': 'bnce', 'd': 'dflt', '-': '----'}
        lp_line_0 = []
        lp_line_1 = []
        half_qp = 4
        for i in range(C.NO_LAYERS):
            cur_clip = self.magi.clip_storage.current_clips[i]
            if cur_clip is None:
                name_line += [" -" * 8]
                cur_pb = '-'
                cur_spd = 0
                cur_sens = 0
                loop_on_off = 2
                loop_no = -1
                loop_type = '-'
                qp_line_0 += ["[_]" for j in range(half_qp)]
                qp_line_1 += ["[_]" for j in range(half_qp)]
                lp_line_0 += ["[_]" for j in range(half_qp)]
                lp_line_1 += ["[_]" for j in range(half_qp)]
            else:
                name_line += ["{:<16}".format(cur_clip.name[:16])]
                cur_pb = cur_clip.params['play_direction']
                cur_spd = cur_clip.params['playback_speed']
                cur_sens = cur_clip.params['control_sens']
                # qp #
                qp = cur_clip.params['cue_points']
                # half_qp = len(qp) // 2
                qp_line_0 += ["[x]" if qp[j] is not None else "[_]"
                              for j in range(half_qp)]
                qp_line_1 += ["[x]" if qp[i + half_qp] is not None else "[_]"
                              for j in range(half_qp)]
                # lp #
                lp = cur_clip.params['loop_points']
                loop_on_off = cur_clip.params['loop_on']
                loop_no = cur_clip.params['loop_selection']
                if loop_no >= 0 and lp[loop_no] is not None:
                    loop_type = lp[loop_no][2]
                else:
                    loop_type = '-'
                lp_line_0 += ["[x]" if lp[j] is not None else "[_]"
                              for j in range(half_qp)]
                lp_line_1 += ["[x]" if lp[i + half_qp] is not None else "[_]"
                              for j in range(half_qp)]
            # ["            : {} ".format()]
            pb_line += ["   dir :  {}     ".format(cur_pb)]
            spd_line += ["   spd : {0: 2.2f}  ".format(cur_spd)]
            sens_line += ["  sens : {0: 2.2f}  ".format(cur_sens)]
            loop_line_0 += ["  loop :  {}   ".format(
                ['off', 'on ', ' - '][loop_on_off])]
            loop_line_1 += ["    {0:2d} :  {1}  ".format(
                loop_no, loop_type_lookup[loop_type])]
            cur_pos = self.magi.model.current_clip_pos[i]
            if cur_pos is None:
                cur_pos = 0.00
            pos_line += ["   pos : {0: .3f} ".format(cur_pos)]
        return " | ".join(name_line) +\
            "\n" + " | ".join(pb_line) + \
            "\n" + " | ".join(pos_line) + \
            "\n" + " | ".join(spd_line) + \
            "\n" + " | ".join(sens_line) + \
            "\nQP:" + "".join(qp_line_0[:half_qp]) + "  |   " + \
            "".join(qp_line_0[half_qp:]) + "\n   " + \
            "".join(qp_line_1[:half_qp]) + "  |   " + \
            "".join(qp_line_1[half_qp:]) + \
            "\n" + " | ".join(loop_line_0) + \
            "\n" + " | ".join(loop_line_1) + \
            "\nLP:" + "".join(lp_line_0[:half_qp]) + "  |   " + \
            "".join(lp_line_0[half_qp:]) + "\n   " + \
            "".join(lp_line_1[:half_qp]) + "  |   " + \
            "".join(lp_line_1[half_qp:])

    def print_cur_col(self):
        cur_col_text = []
        for i in range(len(self.magi.clip_storage.clip_col.clips)):
            cur_col_clip = self.magi.clip_storage.clip_col.clips[i]
            if cur_col_clip is None:
                cur_col_text += ["[ ______________ ]"]
            else:
                cur_col_text += ["[{:<16}]".format(cur_col_clip.name[:16])]
        final_string = ""
        for j in range(len(cur_col_text) // 4):
            for i in range(4):
                indx = 4 * j + i
                if indx < len(cur_col_text):
                    final_string += cur_col_text[indx]
            final_string += "\n"
        return final_string

    def print_cols(self):
        names = [c_c.name for c_c in self.magi.clip_storage.clip_cols]
        names[self.magi.clip_storage.cur_clip_col] = "[{}]".format(
            names[self.magi.clip_storage.cur_clip_col])
        return ' | '.join(names)

    def print_a_line(self):
        return "=" * 73


def main():
    gen_thumbs_flag = False
    if len(sys.argv) > 1:
        if sys.argv[1] in ['help', '-h', '-help']:
            print("""this is the standalone multitouch gui for sol
don't use any flags to run sol in commandline mode with a multitouch client
use -g to generate thumbs to copy to your multitouch client
use -h to get this help screen""")
            sys.exit()
        elif sys.argv[1] in ['thumbs', '-g']:
            gen_thumbs_flag = True
        else:
            print('unknown command "{}"'.format(" ".join(sys.argv[1:])))
            sys.exit()

    testit = Magi()
    testit.gui = MTGui(testit)
    if gen_thumbs_flag:
        testit.gui.gen_thumbs_for_me()
    else:
        testit.start()
        while True:
            try:
                time.sleep(1)
                testit.gui.print_current_state()
            except (KeyboardInterrupt, SystemExit):
                print("exiting...")
                testit.stop()
                break

    testit.save_to_file(testit.db.file_ops.last_save)
