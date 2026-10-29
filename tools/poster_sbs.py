# side-by-side: Jeremy's poster t749 (crop) | mid + deep game shots
import sys
from PIL import Image
L=sys.argv[1];D='/workspace/shark-shots/v10-gfx'
p=Image.open('/workspace/shark-feedback/jeremy-title-art-t749.jpg');k=p.width/473;p=p.crop(tuple(int(v*k) for v in (32,130,442,742)))
ims=[Image.open(f'{D}/{L}-915x412-{n}.png') for n in ('mid','deep')];H=900
ims=[i.resize((int(i.width*H/2/i.height),H//2)) for i in ims];p=p.resize((int(p.width*H/p.height),H))
o=Image.new('RGB',(p.width+ims[0].width,H));o.paste(p,(0,0));o.paste(ims[0],(p.width,0));o.paste(ims[1],(p.width,H//2));o.save(f'{D}/{L}-vs-t749-poster.png');print(f'{D}/{L}-vs-t749-poster.png')
