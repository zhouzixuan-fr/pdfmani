import pikepdf
import re
import pymupdf

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

if __name__ == '__main__':
    import sys

    script_name = sys.argv[0]
    args = sys.argv[1:]

    if len(args) < 2:
        print("usage: pdfmani <input> <TOC filename>")
        exit()

    input_fn, TOC_fn = args 
    add_TOC(input_fn, TOC_fn)

    #add_TOC("input.pdf", "TOC.txt")
    #add_splitline("t2.pdf")
    #split_and_crop("t2.pdf")
    
