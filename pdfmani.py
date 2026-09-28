import pikepdf
import re
import pymupdf
from pprint import pprint

#magical regex GPT-4o gave me :)
def parse_line(line):
    pattern = r"^(?P<indent>\t*)(?P<title>.*?)\s+(?P<page>\d+)\s*$"
    match = re.match(pattern, line)
    if match:
        return (
            len(match.group("indent")),
            match.group("title"),
            int(match.group("page"))
            )
    return None

#clever stack logic GPT-4o gave me :)
def parse_toc(toc_lines):
    root = []
    stack = []  # Stack of (indent_level, pikepdf.OutlineItem)

    print("indent title page")
    for line in toc_lines:

        #indent = len(line) - len(line.lstrip(' \t'))
        #title, page = line.strip().rsplit('\t', 1)

        #indent, title, page = parse_line(line)
        try:
            indent, title, page = parse_line(line)
        except Exception as e:
            #TODO handle empty line
            print(f"error is {e}")
            exit()

        #print(f"indent={indent}, title={title}, page={page}")
        print(indent, title, page)
        page_num = int(page) - 1  # pikepdf 是 zero-based

        item = pikepdf.OutlineItem(title, page_num)

        # 檢查插入到哪個層級
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if not stack:
            root.append(item)
        else:
            stack[-1][1].children.append(item)

        stack.append((indent, item))

    return root


def debug(x):
    print(x)
    print(type(x))
    print(dir(x))


def merge_pdf(pdf_fn1, pdf_fn2, output_fn="output.pdf"):
    pdf1 = pikepdf.Pdf.open(pdf_fn1)
    pdf2 = pikepdf.Pdf.open(pdf_fn2)
    pdf1.pages.extend(pdf2.pages)
    pdf1.save(output_fn)


def add_TOC(pdf_fn, TOC_fn, output_fn="output.pdf"):
    pdf = pikepdf.Pdf.open(pdf_fn)
    #exit()

    with open(TOC_fn, "r", encoding="utf-8") as f:
        toc_lines = f.readlines()
    
    outline_items = parse_toc(toc_lines)
    #debug(outline_items[0].children)
    
    with pdf.open_outline() as outline:
        debug(outline.root)
        outline.root.clear()
        debug(outline.root)
        outline.root.extend(outline_items)
        debug(outline.root)
    pdf.save(output_fn)

def extract_TOC(pdf_fn, TOC_output_fn):
    pdf = pikepdf.Pdf.open(pdf_fn)
    #debug(pdf)
    pdf2 = pymupdf.open(pdf_fn)
    #debug(pdf2)
    #debug(pdf2.get_toc())
    TOC = pdf2.get_toc()
    #pprint(TOC)
    with open(TOC_output_fn, "w", encoding="utf-8") as f:

        for line in TOC:
            depth, title, page_num = int(line[0])-1, line[1].strip(), line[2]
            x = depth*"\t" + f'{title} {page_num}\n'
            f.write(x)



def add_splitline(pdf_fn, output_fn="output.pdf"):
    # 開啟 PDF
    pdf = pymupdf.open(pdf_fn)
    
    for page in pdf:
        rect = page.rect
        mid_x = rect.width / 2
    
        # 畫一條中間的垂直線，從頂到底
        page.draw_line(
            p1=(mid_x, 0),
            p2=(mid_x, rect.height),
            color=(1, 0, 0),  # 紅色線條
            width=1
        )
    # 儲存結果
    pdf.save(output_fn)
    
def split_and_crop(pdf_fn, output_fn="output.pdf"):

    # 開啟原始 PDF
    pdf = pymupdf.open(pdf_fn)
    
    new_pdf = pymupdf.open()  # 新 PDF

    #pages with no need to split
    new_pdf.insert_pdf(pdf, from_page=0, to_page=2)
    
    for page in pdf:

        if page.number < 3 or page.number == 143:
            continue

        print(page.number)
        rect = page.rect
        # split simply by mid
        mid_x = rect.width / 2
    
        #Rect(左, 下, 右, 上)
        bottom_trim = 150
        top_trim = 150
        #debug(rect)
        # 左半頁
        left_rect = pymupdf.Rect(0, 0 + bottom_trim, mid_x, rect.height - top_trim)
        left_page = new_pdf.new_page(width=left_rect.width, height=left_rect.height)
        left_page.show_pdf_page(left_page.rect, pdf, page.number, clip=left_rect)
    
        # 右半頁
        right_rect = pymupdf.Rect(mid_x, 0 + bottom_trim, rect.width, rect.height - top_trim)
        right_page = new_pdf.new_page(width=right_rect.width, height=right_rect.height)
        right_page.show_pdf_page(right_page.rect, pdf, page.number, clip=right_rect)
    
    new_pdf.insert_pdf(pdf, from_page=143, to_page=143)
    # 儲存新 PDF
    new_pdf.save(output_fn)


def select(input_fn, selected_pages):
    src_pdf = pikepdf.Pdf.open(input_fn)

    new_pdf = pikepdf.Pdf.new()
    new_pdf.pages.extend(src_pdf.pages.p(i) for i in selected_pages)
    new_pdf.save("output.pdf")


def merge_as(input_fn, merge_as_pages):
    src_pdf = pikepdf.Pdf.open(input_fn)

    new_pdf = pikepdf.Pdf.new()

    for merge_tuple in merge_as_pages:

        a, b = src_pdf.pages.p(merge_tuple[0]), src_pdf.pages.p(merge_tuple[1])
        w, h = float(a.mediabox[2]), float(a.mediabox[3])

        new_page = new_pdf.add_blank_page(page_size=(w, h*2))
        new_page.add_overlay(b, pikepdf.Rectangle(0, 0, w, h))        # 上
        new_page.add_overlay(a, pikepdf.Rectangle(0, h, w, h*2))    # 下

        #new_pdf.pages.extend(new_page)

    new_pdf.save("output.pdf")


if __name__ == '__main__':
    import sys

    script_name = sys.argv[0]
    args = sys.argv[1:]

    if len(args) < 2:
        print("usage: pdfmani <input> <TOC filename>")
        #exit()

    #add TOC 
    if True:
        #input_fn, TOC_fn = args 
        input_fn, TOC_fn = "input.pdf", "TOC.txt"
        add_TOC(input_fn, TOC_fn)

    #extract TOC
    if False:
        extract_TOC("input.pdf", "TOC.txt")

    #add_TOC("input.pdf", "TOC.txt")
    #add_splitline("t2.pdf")
    #split_and_crop("t2.pdf")

    #select("input.pdf", 
    #[2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24, 26, 27, 29, 30, 32, 33, 35, 36, 38, 39, 41, 42, 44, 45, 47, 48, 50, 51, 53, 54, 56, 57, 59, 60, 62, 63, 65, 66, 68, 69, 71, 72, 74, 75, 77, 78, 80, 81]
    #)

    #merge_as("input.pdf", 
    #[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16), (17, 18), (19, 20), (21, 22), (23, 24), (25, 26), (27, 28), (29, 30), (31, 32), (33, 34), (35, 36), (37, 38), (39, 40), (41, 42), (43, 44), (45, 46), (47, 48), (49, 50), (51, 52), (53, 54)]
    #)
