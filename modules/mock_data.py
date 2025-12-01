"""
Mock Data Generator
Generates realistic test data for development and testing
"""

import pandas as pd
import random


def generate_mock_data() -> pd.DataFrame:
    """
    Generate mock switching analysis data for testing
    
    Returns:
        pd.DataFrame: Mock data with columns: prod_2024, prod_2025, customers, move_type
    """
    brands = ['NIVEA', 'VASELINE', 'CITRA']
    special_categories = ['NEW_TO_CATEGORY', 'LOST_FROM_CATEGORY', 'MIXED']
    
    data = []
    
    # Generate stayed customers
    for brand in brands:
        customers = random.randint(15000, 30000)
        data.append({
            'prod_2024': brand,
            'prod_2025': brand,
            'customers': customers,
            'move_type': 'stayed'
        })
    
    # Generate switched customers (brand to brand)
    for from_brand in brands:
        for to_brand in brands:
            if from_brand != to_brand:
                customers = random.randint(2000, 8000)
                data.append({
                    'prod_2024': from_brand,
                    'prod_2025': to_brand,
                    'customers': customers,
                    'move_type': 'switched'
                })
    
    # Generate new to category
    for brand in brands:
        customers = random.randint(5000, 15000)
        data.append({
            'prod_2024': 'NEW_TO_CATEGORY',
            'prod_2025': brand,
            'customers': customers,
            'move_type': 'new_to_category'
        })
    
    # Generate lost from category
    for brand in brands:
        customers = random.randint(3000, 10000)
        data.append({
            'prod_2024': brand,
            'prod_2025': 'LOST_FROM_CATEGORY',
            'customers': customers,
            'move_type': 'lost_from_category'
        })
    
    # Generate MIXED scenarios
    for brand in brands:
        # MIXED to brand (switch in)
        customers = random.randint(1000, 5000)
        data.append({
            'prod_2024': 'MIXED',
            'prod_2025': brand,
            'customers': customers,
            'move_type': 'switched'
        })
        
        # Brand to MIXED (switch out)
        customers = random.randint(1000, 5000)
        data.append({
            'prod_2024': brand,
            'prod_2025': 'MIXED',
            'customers': customers,
            'move_type': 'switched'
        })
    
    # MIXED stayed
    data.append({
        'prod_2024': 'MIXED',
        'prod_2025': 'MIXED',
        'customers': random.randint(5000, 12000),
        'move_type': 'stayed'
    })
    
    # NEW to MIXED
    data.append({
        'prod_2024': 'NEW_TO_CATEGORY',
        'prod_2025': 'MIXED',
        'customers': random.randint(2000, 6000),
        'move_type': 'new_to_category'
    })
    
    # MIXED to LOST
    data.append({
        'prod_2024': 'MIXED',
        'prod_2025': 'LOST_FROM_CATEGORY',
        'customers': random.randint(2000, 6000),
        'move_type': 'lost_from_category'
    })
    
    df = pd.DataFrame(data)
    return df


def get_mock_categories() -> list:
    """Get list of categories"""
    return [
        'BEAUTY ACCESSORIES', 'BLADES', 'BODY SCRUB', 'COLOGNE', 'CONDITIONER',
        'CONDOM', 'DENTAL FLOSS', 'DEODODRANT', 'FACIAL CLEANSING', 'FOOD SUPPLEMENT',
        'FRAGRANCE', 'HAIR COLORING', 'HAIR STYLING', 'HERBAL', 'LIQUID SOAP',
        'MAKE UP BASE', 'MAKE UP COLOUR', 'MAKE UP EYE&EYEBROW',  'MAKE UP LIPS',
        'MAKE UP NAILS', 'MAKE UP OTHER', 'MAKE UP POWDER', 'MASK', 'MEDICINE CABINET',
        'MOISTURIZER FOR BODY', 'MOISTURIZER FOR FACE', 'MOUTHWASH', 'RAZORS',
        'SANITARY PROTECTION-NAPKIN', 'SANITARY PROTECTION-PLN', 'SHAMPOO', 'SKIN HAIR',
        'SUNCARE', 'TALCUM POWDER', 'TOILET SOAP', 'TOOTHBRUSH', 'TOOTHPASTE'
    ]


def get_mock_subcategories(category: str) -> list:
    """Get list of subcategories for a category"""
    subcategory_mapping = {
        'BEAUTY ACCESSORIES': ['ACCESSORIES FOR BODY', 'ACCESSORIES FOR FACE', 'ACCESSORIES FOR HAIR', 'SPECIAL'],
        'BLADES': ['DISPOSABLE', 'DOUBLE EDGE', 'SYSTEM'],
        'BODY SCRUB': ['HERBAL', 'LIQUID SOAP', 'SPA SALT'],
        'COLOGNE': ['LADIES', 'MEN'],
        'CONDITIONER': ['ANTI DDF.', 'CONDITIONER', 'HERBAL', 'SUPER TREATMENT'],
        'CONDOM': ['FLAVOR CONDOM', 'SPECIAL CONDOM', 'STANDARD CONDOM', 'TEXTURE CONDOM'],
        'DENTAL FLOSS': ['MENTHOL', 'OTHER'],
        'DEODODRANT': ['POWDER', 'ROLL ON-LADIES', 'ROLL ON-MEN', 'SPARY-LADIES', 'SPARY-MEN', 'SPECIAL', 'STICK-LADIES', 'STICK-MEN'],
        'FACIAL CLEANSING': ['FOAM', 'GEL', 'MAKE UP REMOVER', 'MEN', 'OIL', 'SCRUB', 'SOAP', 'SPECIAL', 'WATER', 'WIPE OFF'],
        'FOOD SUPPLEMENT': ['BEAUTY', 'DIETARY', 'HERBAL', 'HOT DRINK', 'SPECIAL', 'VITAMIN'],
        'FRAGRANCE': ['EAU DE COLOGEN (EDC)', 'EAU DE PERFUME (EDP)', 'EAU DE TOILETTE EDT'],
        'HAIR COLORING': ['BLEACHING', 'HAIR STRAIGHT', 'PERMANENT', 'PERMANENT WAVES', 'SEMI PERMANENT', 'SHAMPOO', 'SPECIAL'],
        'HAIR STYLING': ['CREAM', 'FOAM/MOUSSE', 'GEL', 'HAIR COAT', 'OIL', 'SPRAY', 'WAX'],
        'HERBAL': ['HERBAL FACIAL CLEAN', 'HERBAL HAIR TREATMET', 'HERBAL MASK', 'HERBAL MOISTURIZER', 'HERBAL ORAL CARE', 'HERBAL OTHER', 'HERBAL SCRUB', 'HERBAL SHAMPOO', 'HERBAL SOAP'],
        'LIQUID SOAP': ['BABY', 'BASIC CARE', 'HEALTH', 'HERBAL', 'INTIMATE WASH', 'MEN', 'SANITIZER', 'SPECIAL'],
        'MAKE UP BASE': ['AA/BB/CC/DD', 'BASE', 'CONCEALER', 'FOUNDATION', 'PRIMER', 'SPECIAL'],
        'MAKE UP COLOUR': ['COLOUR', 'HIGHLIGHT', 'SHADING', 'SPECIAL'],
        'MAKE UP EYE&EYEBROW': ['EYEBROW', 'EYELINER', 'EYESHADOW', 'MASCARA', 'SPECIAL'],
        'MAKE UP LIPS': ['LIP BALM', 'LIP GLOSS', 'LIP LINER', 'LIP TINT', 'LIPSTICK', 'SPECIAL'],
        'MAKE UP NAILS': ['NAIL POLISH', 'NAIL POLISH REMOVER'],
        'MAKE UP OTHER': ['HERBAL & TRADITION', 'OTHER', 'SPECIAL'],
        'MAKE UP POWDER': ['FOUNDATION POWDER', 'LOOSE POWDER', 'PRESSED POWDER', 'SPECIAL'],
        'MASK': ['PEEL OFF', 'RINES OFF', 'SCRUB', 'SPECIAL', 'TISSUE MASK'],
        'MEDICINE CABINET': ['EXTERNAL', 'INTERNAL', 'MEDICAL SUPPLY'],
        'MOISTURIZER FOR BODY': ['ADVANCE BENEFITS', 'BASIC CARE', 'FIRMING CREAM', 'FOOTSOFTCREAM', 'PERFUME', 'SPECIAL', 'UNDERARM', 'UV PROTECTION', 'WHITENING'],
        'MOISTURIZER FOR FACE': ['ANTI ACNE FULLFACE', 'ANTI-AGING', 'ANTIACNE SPOT TREAT.', 'BASIC CARE', 'EYE', 'MELASMA', 'MEN', 'SPECIAL', 'TONER', 'UV PROTECTION', 'WHITENING'],
        'MOUTHWASH': ['ADULT', 'BABY', 'MOUTH SPRAY'],
        'RAZORS': ['DOUBLE EDGE', 'SPECIAL', 'SYSTEM'],
        'SANITARY PROTECTION-NAPKIN': ['DAYS', 'NIGHTS', 'PANTS'],
        'SANITARY PROTECTION-PLN': ['SCENTED', 'SLIM', 'TEMPON', 'UNSCENTED'],
        'SHAMPOO': ['ANTI DDF.', 'BABY', 'BASIC CARE', 'HERBAL', 'MEN', 'SPECIAL'],
        'SKIN HAIR': ['Bleaching', 'CREAM REMOVAL', 'WAX REMOVAL'],
        'SUNCARE': ['BODY SUN CARE', 'FACIAL SUN CARE', 'SPECIAL'],
        'TALCUM POWDER': ['BABY', 'BEAUTY', 'LIQUID', 'MEN', 'MENTHOL', 'SPECIAL'],
        'TOILET SOAP': ['BABY', 'BASIC CARE', 'HEALTH', 'HERBAL', 'MEN', 'SPECIAL'],
        'TOOTHBRUSH': ['AUTOMATIC', 'BABY', 'ORTHODONTIC', 'SPRICIAL', 'STANDARD'],
        'TOOTHPASTE': ['HERBALTRADITIONAL', 'KIDS', 'REGULAR', 'THERAPEUTIC', 'WHITENING']
    }
    return subcategory_mapping.get(category, [])


def get_mock_brands(category: str) -> list:
    """Get list of mock brands for a category"""
    brand_mapping = {
        'MOISTURIZER FOR BODY': ['NIVEA', 'VASELINE', 'CITRA', 'JERGENS'],
        'FACIAL CLEANSING': ['NIVEA', 'CETAPHIL', 'CLEAN & CLEAR', 'GARNIER'],
        'SHAMPOO': ['CLEAR', 'PANTENE', 'HEAD & SHOULDERS', 'DOVE'],
        'TOILET SOAP': ['DOVE', 'LUX', 'NIVEA', 'JOHNSONS'],
        'DEODODRANT': ['NIVEA', 'REXONA', 'AXE', 'DOVE']
    }
    return brand_mapping.get(category, ['NIVEA', 'VASELINE', 'CITRA'])


def get_example_barcode_mapping() -> str:
    """Get example barcode mapping text"""
    return """8850999320027,Premium Products
8851234567890,Budget Products
8852345678901,Mid-range Products
8853456789012,Economy Products
8854567890123,Luxury Products"""
