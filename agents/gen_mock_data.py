"""
Generate mock data for PulseAI demo scenario.
"""
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from pypdf import PdfReader, PdfWriter

log = structlog.get_logger()

# Fixed reference date to ensure deterministic date strings
REFERENCE_TODAY = datetime(2026, 5, 17, tzinfo=timezone.utc)

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def generate_monthly_sales_pdf(output_dir: Path, outlier: str, stable: list):
    pdf_path = output_dir / "monthly_regional_sales.pdf"
    temp_pdf_path = output_dir / "temp_sales.pdf"
    
    doc = SimpleDocTemplate(str(temp_pdf_path), pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Monthly Regional Sales Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    data = [["Region", "Orders", "Revenue (PKR)", "YoY% Growth"]]
    
    # Sort regions to ensure deterministic order
    all_regions = sorted([outlier] + stable)
    
    for r in all_regions:
        orders = random.randint(1000, 5000)
        revenue = orders * random.randint(3500, 5500)
        if r == outlier:
            growth = "+5%"
        else:
            g = random.randint(-3, 7)
            growth = f"+{g}%" if g > 0 else f"{g}%"
            if g == 0:
                growth = "0%"
                
        data.append([r, str(orders), f"{revenue:,}", growth])
        
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    # Update metadata with pypdf
    creation_date = REFERENCE_TODAY - timedelta(days=30)
    formatted_date = creation_date.strftime("D:%Y%m%d%H%M%S+00'00'")
    
    reader = PdfReader(str(temp_pdf_path))
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
        
    metadata = reader.metadata
    if metadata:
        writer.add_metadata(metadata)
    writer.add_metadata({"/CreationDate": formatted_date})
    
    with open(pdf_path, "wb") as f:
        writer.write(f)
        
    temp_pdf_path.unlink()
    log.info("Generated PDF", file=pdf_path.name)

def generate_pos_ecom_csv(output_dir: Path, outlier: str, stable: list):
    csv_path = output_dir / "pos_ecom_last_30d.csv"
    
    records = []
    all_regions = sorted([outlier] + stable)
    
    for i in range(30):
        current_date = (REFERENCE_TODAY - timedelta(days=30 - i)).strftime("%Y-%m-%d")
        
        for region in all_regions:
            for channel in ["pos", "ecom"]:
                base_orders = int(np.random.randint(80, 180))
                noise = np.random.uniform(-0.05, 0.05)
                orders = base_orders * (1 + noise)
                
                if region == outlier:
                    if i >= 16:
                        drop = np.random.uniform(0.20, 0.35)
                    else:
                        drop = np.random.uniform(0.10, 0.20)
                    orders = orders * (1 - drop)
                
                orders = max(1, int(orders))
                basket = int(np.random.randint(3500, 5500))
                revenue = orders * basket
                
                records.append({
                    "date": current_date,
                    "region": region,
                    "channel": channel,
                    "orders": orders,
                    "revenue_pkr": revenue,
                    "avg_basket_pkr": basket
                })
                
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)
    log.info("Generated CSV", file=csv_path.name, rows=len(df))

def generate_news_expansion(output_dir: Path, outlier: str, competitor: dict):
    html_path = output_dir / "news_competitor_expansion.html"
    date_str = (REFERENCE_TODAY - timedelta(days=25)).strftime("%B %d, %Y")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{competitor['name']} Opens {competitor['stores_opened']} New Stores in {outlier}, Targets Young Women's Casual Segment</title>
</head>
<body>
    <h1>{competitor['name']} Opens {competitor['stores_opened']} New Stores in {outlier}, Targets Young Women's Casual Segment</h1>
    <p>By Reuters Pakistan | {date_str}</p>
    <p>In a major retail expansion, {competitor['name']} has announced the opening of {competitor['stores_opened']} new stores in the bustling region of {outlier}. This move, planned since {competitor['expansion_month']}, marks a significant step in the brand's aggressive growth strategy.</p>
    <p>Targeting the lucrative "women's casual wear" segment, particularly ages 22 to 32, {competitor['name']} is rolling out a pricing model that boasts an estimated {competitor['pricing_advantage_pct']}% pricing advantage over its major rivals.</p>
    <p>{"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 30}</p>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    log.info("Generated HTML", file=html_path.name)

def generate_analytics(output_dir: Path, outlier: str, stable: list):
    json_path = output_dir / "analytics_by_region.json"
    records = []
    
    all_regions = sorted([outlier] + stable)
    
    for i in range(30):
        current_date = (REFERENCE_TODAY - timedelta(days=30 - i)).strftime("%Y-%m-%d")
        
        for region in all_regions:
            reach = int(np.random.randint(50000, 100000))
            sentiment = np.random.uniform(0.70, 0.85)
            cr = np.random.uniform(0.01, 0.03)
            
            reach = int(reach * (1 + np.random.uniform(-0.02, 0.02)))
            
            if region == outlier:
                if i >= 20:
                    reach = int(reach * 0.60)
                    sentiment -= 0.15
                    
            records.append({
                "date": current_date,
                "region": region,
                "reach": reach,
                "sessions": int(reach * 0.1),
                "conversion_rate": round(cr, 4),
                "sentiment_score": round(sentiment, 2)
            })
            
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    log.info("Generated JSON", file=json_path.name)

def generate_support_tickets(output_dir: Path, outlier: str, stable: list):
    jsonl_path = output_dir / "support_tickets.jsonl"
    all_regions = sorted([outlier] + stable)
    
    tickets = []
    for t_id in range(1, 201):
        day_offset = random.randint(1, 30)
        t_date = (REFERENCE_TODAY - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        region = random.choice(all_regions)
        
        cat = "delivery"
        if region == outlier and day_offset <= 14:
            if random.random() < 0.30:
                cat = random.choice(["pricing", "competitor_mention"])
            else:
                cat = random.choice(["delivery", "quality", "sizing"])
        else:
            if random.random() < 0.05:
                cat = random.choice(["pricing", "competitor_mention"])
            else:
                cat = random.choice(["delivery", "quality", "sizing"])
                
        sentiment = round(random.uniform(0.1, 0.5), 2)
        
        snippets = {
            "delivery": ["Where is my order?", "Taking too long."],
            "quality": ["Stitching is bad.", "Color faded after one wash."],
            "sizing": ["Too small.", "Doesn't fit right."],
            "pricing": ["Too expensive now.", "Prices are ridiculous."],
            "competitor_mention": ["TrendyPK has better prices.", "Switching to TrendyPK."]
        }
        text = random.choice(snippets[cat])
        
        tickets.append({
            "ticket_id": f"TKT-{t_id:04d}",
            "date": t_date,
            "region": region,
            "category": cat,
            "sentiment": sentiment,
            "text": text
        })
        
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for t in tickets:
            f.write(json.dumps(t) + "\n")
            
    log.info("Generated JSONL", file=jsonl_path.name, lines=len(tickets))

def generate_marketing_spend(output_dir: Path, outlier: str, stable: list):
    json_path = output_dir / "marketing_spend.json"
    all_regions = sorted([outlier] + stable)
    month_str = REFERENCE_TODAY.strftime("%Y-%m")
    
    spend = {
        "month": month_str,
        "regions": {}
    }
    
    for region in all_regions:
        base = 100000
        if region == outlier:
            factor = 2.5
        else:
            factor = random.uniform(0.8, 1.2)
            
        spend["regions"][region] = {
            "google_ads": int(base * factor),
            "meta_ads": int(base * factor * 1.2),
            "tiktok": int(base * factor * 0.8),
            "influencer": int(base * factor * 0.5)
        }
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spend, f, indent=2)
    log.info("Generated JSON", file=json_path.name)

def generate_throw_ins(output_dir: Path):
    blog_path = output_dir / "news_pricing_blog.html"
    social_path = output_dir / "social_post_spam.json"
    
    blog_html = f"""<!DOCTYPE html>
<html>
<head><title>Are TrendyPK Prices Really Cheaper? My Comparison</title></head>
<body>
    <h1>Are TrendyPK Prices Really Cheaper? My Comparison</h1>
    <p>I went to the store today and I CANNOT BELIEVE what I saw! Everybody says TrendyPK is cheaper but honestly the pricing is roughly similar! Don't believe the hype people!</p>
    <p>{"BUY BUY BUY " * 20}</p>
</body>
</html>
"""
    with open(blog_path, "w", encoding="utf-8") as f:
        f.write(blog_html)
    log.info("Generated HTML", file=blog_path.name)
        
    social_data = {
        "platform": "instagram",
        "handle": "spammy_bot_99",
        "text": "ACT NOW!!! 🚨🚨 DM me for limited time offers!! 💸💸💸",
        "posted_at": REFERENCE_TODAY.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(social_path, "w", encoding="utf-8") as f:
        json.dump(social_data, f, indent=2)
    log.info("Generated JSON", file=social_path.name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, help="Seed name (e.g. lahore, karachi)")
    args = parser.parse_args()
    
    seed_name = args.seed
    
    random.seed(42)
    np.random.seed(42)
    
    workspace = Path(__file__).resolve().parent.parent
    seed_file = workspace / "sources" / "zarapk_regional_v1" / f"{seed_name}.seed.json"
    
    if not seed_file.exists():
        log.error("Seed file not found", path=str(seed_file))
        return
        
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_data = json.load(f)
        
    outlier = seed_data["outlier_region"]
    stable = seed_data["stable_regions"]
    competitor = seed_data["competitor"]
    
    output_dir = workspace / "sources" / "zarapk_regional_v1" / seed_name
    ensure_dir(output_dir)
    
    log.info("Generating mock data", seed=seed_name, outlier=outlier)
    
    generate_monthly_sales_pdf(output_dir, outlier, stable)
    generate_pos_ecom_csv(output_dir, outlier, stable)
    generate_news_expansion(output_dir, outlier, competitor)
    generate_analytics(output_dir, outlier, stable)
    generate_support_tickets(output_dir, outlier, stable)
    generate_marketing_spend(output_dir, outlier, stable)
    generate_throw_ins(output_dir)
    
    log.info("Mock data generation complete", output_dir=str(output_dir))

if __name__ == "__main__":
    main()
