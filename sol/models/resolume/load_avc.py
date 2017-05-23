import xml.etree.ElementTree as ET
import os

class ResolumeLoader:
    """
    reads .avc and gets the clips out of them
    tested on resolume arena 5 (& 4) may break in the future

    maybe add check to see if proper hack setup is done
    if not offer to do it for them =)
    """
    def __init__(self):
        self.clips = {}
    
    def import_xml(self,xmlfile):
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        
        # general info
        gen_info = [gi for gi in root.iter('generalInfo')][0].attrib
        comp_name = gen_info['name']
        comp_w, comp_h = gen_info['width'], gen_info['height']
        deck_count = gen_info['deckCount']
        if eval(deck_count) > 1:
            print("incorrect setup! please use only 1 deck")

        # lets get to the clips 
        decks = [deck for deck in \
                 [d for d in root.iter('decks')][0].iter('deck')]
        xml_clips = decks[0].findall('clip')

        for xml_clip in xml_clips:
            # layer/clip are 0 indexed in xml file but osc command
            # is 1 indexed (nice consistency)
            l = eval(xml_clip.get('layerIndex')) + 1
            c = eval(xml_clip.get('trackIndex')) + 1
            command = "/layer{0}/clip{1}/connect".format(l,c)

            name = xml_clip[0][1].get('value')
            f_name = xml_clip[1][0].get('name')
        
            # params
            params = {}
            xml_param = xml_clip[1][1].find('parameters')[0]
            try:
                pbs = eval(xml_param.find('speedFactor').get('curValue'))
            except:
                pbs = 1.0
            params['playback_speed'] = pbs
            direction_lookup = ['b','f','p','r']
            try:
                # fix this... not working >:(
                p_dir_i = eval(xml_param.find('playmode').get('value'))
            except:
                p_dir_i = 2
            params['play_direction'] = direction_lookup[p_dir_i]

            # queue points already present
            # xml_clip[1][1][2][0][0][6] .findall('choice') .get('value')

            # now to figure out how to create clips properly from this
            self.clips[f_name] = (f_name, command, name,None, # none because no thumb yet
                        params) 

    def export_subset(self,xmlfile,output_xml=None,clip_fnames=[]):
        if output_xml is None or len(output_xml)==0:
            reversed_outputname = xmlfile[::-1]
            output_xml = reversed_outputname[reversed_outputname.index('.')+1:][::-1] + '_just_collections.avc'
        # check for proper extension    
        else:
            if output_xml[-4:] != '.avc':
                output_xml += '.avc'
        if os.path.exists(output_xml):
            os.remove(output_xml)

        tree = ET.parse(xmlfile)
        root = tree.getroot()

        decks = [deck for deck in \
                 [d for d in root.iter('decks')][0].iter('deck')]
        for deck in decks:
            xml_clips = deck.findall('clip')
            for clip in xml_clips:
                try:
                    clip_fname = clip[1][0].get('name')
                    if clip_fname not in clip_fnames:
                        deck.remove(clip)
                except Exception as e:
                    pass
        tree.write(output_xml)
        print('successfully exported',output_xml)


if __name__ == '__main__':
    # testfile = "C:/Users/shapil/Documents/Resolume Arena 5/compositions/example.avc"
    testfile = "C:/Users/Leo/Documents/Resolume Arena 5/compositions/vjcomp.avc"


    test_loader = ResolumeLoader()

    test_clip_fnames = ['C:\\VJ\\__clips__\\artsy\\dxv\\Haruhi Spooky Dance.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\boot tap.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\Adam Eve.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\nuke boom.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\Rainy Un Soldier.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\sayonara zetsubou sensei moth goodbye.mov', 'C:\\VJ\\__clips__\\artsy\\dxv\\Warning.mov', 'C:\\VJ\\__clips__\\grils\\dxv\\cyberpunk girl thing.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Macross Frontier Singing Gril.mov', 'C:\\VJ\\__clips__\\grils\\dxv\\Macross Singing Gril.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Macross Dynamite Music Power.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Macross Target N Transform.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Rock On.mov', 'C:\\VJ\\__clips__\\grils\\dxv\\Photo Frame.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Macross Guitar Listen To My Song.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Macross Space Station Battle.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Space Plane Dodge N Transform.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Space Fight Lots Of Mechs Dyin.mov', 'C:\\VJ\\__clips__\\mecha\\dxv\\Space Ship Grils Missiles Etc.mov']

    # test_loader.export_subset(testfile,clip_fnames=test_clip_fnames)
    print(testfile[-4:])

