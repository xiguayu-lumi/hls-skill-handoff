"""Typeset a white-header, color-block illustration cover from a JSON specification."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

def load_font(path, size, bold=False):
    f = ImageFont.truetype(str(path), int(size))
    if bold:
        try:
            f.set_variation_by_name("Black")
        except (AttributeError, OSError, ValueError):
            pass
    return f

def render(spec_path, output):
    spec_path, output = Path(spec_path).resolve(), Path(output).resolve()
    s = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    if s.get("canvas", [1080,1440]) != [1080,1440]:
        raise ValueError("This template uses 1080x1440")
    py = s.get("panel_y",720)
    if not isinstance(py,int) or not 660 <= py <= 790:
        raise ValueError("panel_y must be 660..790")
    lines = s["headline_lines"]
    sizes, ys = s["headline_sizes"], s["headline_y"]
    if not 2 <= len(lines) <= 3 or len(lines) != len(sizes) or len(lines) != len(ys):
        raise ValueError("Provide 2-3 headline lines with matching sizes and y positions")
    if len(s.get("english_lines",[])) > 2:
        raise ValueError("At most two English lines")
    def resolve(p):
        p = Path(p)
        return p if p.is_absolute() else spec_path.parent/p
    fonts = {k:resolve(v) for k,v in s["fonts"].items()}
    image_path = resolve(s["image"])
    if output == image_path.resolve() or output.exists():
        raise ValueError("Use a new output version; source and existing files are protected")
    im = Image.new("RGB",(1080,1440),"white")
    draw = ImageDraw.Draw(im)
    boxes=[]
    def write(text,xy,size,kind="cn",color="#111111",headline=False):
        if not isinstance(text,str) or not text.strip():
            raise ValueError("Text must be a nonempty string")
        if not 18 <= size <= 160:
            raise ValueError("Font size outside supported range")
        f=load_font(fonts[kind],size,True)
        if headline:
            while draw.textlength(text,font=f)>976 and size>90:
                size-=1;f=load_font(fonts[kind],size,True)
            if size<90:
                raise ValueError("Headline must remain at least 90px; reword or reflow")
        b=draw.textbbox(xy,text,font=f,anchor="lt")
        if b[0]<40 or b[2]>1040 or b[1]<20 or b[3]>=py-20:
            raise ValueError(f"Text overflows available area: {text}")
        for previous in boxes:
            c=previous["box"]
            if b[0]<c[2] and b[2]>c[0] and b[1]<c[3]+8 and b[3]+8>c[1]:
                raise ValueError(f"Text overlaps another line: {text}")
        draw.text(xy,text,font=f,fill=color,anchor="lt")
        boxes.append(dict(text=text,box=b,size=size))
    write(s["masthead"],(52,30),58,"en")
    if s.get("category"):
        write(s["category"],(807,49),25,color="#515151")
    draw.line((52,106,1028,106),fill="#202020",width=2)
    for i,line in enumerate(s.get("english_lines",[])):
        write(line,(52,135+i*43),35,"en",s.get("accent","#BA3529"))
    for line,size,y in zip(lines,sizes,ys):
        if y<230:
            raise ValueError("Headline must start below header")
        write(line,(52,y),size,headline=True)
    art=Image.open(image_path).convert("RGBA")
    fitted=ImageOps.contain(art,(1080,1440-py),Image.Resampling.LANCZOS)
    panel=Image.new("RGB",(1080,1440-py),s["panel_color"])
    panel.paste(fitted,((1080-fitted.width)//2,(1440-py-fitted.height)//2),fitted)
    im.paste(panel,(0,py))
    output.parent.mkdir(parents=True,exist_ok=True)
    im.save(output,format="PNG")
    report=dict(canvas=im.size,panel_y=py,text_boxes=boxes,fonts={k:str(v) for k,v in fonts.items()},source_image=str(image_path),source_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),visual_review="pending")
    output.with_suffix(".layout.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

if __name__ == "__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec",required=True);ap.add_argument("--output",required=True)
    a=ap.parse_args();render(a.spec,a.output);print(a.output)
