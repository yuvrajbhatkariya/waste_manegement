import os
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import numpy as np

class WasteGuidance:
    def __init__(self, static_folder='static'):
        self.static_folder = static_folder
        self.guidance_folder = os.path.join(static_folder, 'guidance')
        self.waste_types = self._get_waste_types()  # Use internal method
        self.guidance_data = self._initialize_guidance_data()  # Use internal data
        self.ensure_folders_exist()
        self.ensure_guidance_images()
        
    def ensure_folders_exist(self):
        """Ensure that necessary folders for guidance images exist"""
        if not os.path.exists(self.guidance_folder):
            os.makedirs(self.guidance_folder)
            
    def _get_waste_types(self):
        """Get list of waste types from guidance data"""
        return list(self._initialize_guidance_data().keys())

    def _initialize_guidance_data(self):
        """Initialize guidance data for different waste types"""
        guidance_data = {
            'Automobile Waste': {
                'steps': [
                    'Separate fluids (oil, coolant, brake fluid) into appropriate containers',
                    'Take batteries to authorized recycling centers',
                    'Recycle metal components at scrap yards',
                    'Dispose of tires at tire recycling facilities'
                ],
                'colors': ['#E63946', '#F1FAEE', '#A8DADC', '#457B9D', '#1D3557'],
                'icon': '🚗'
            },
            'Electronic Waste': {
                'steps': [
                    'Remove batteries and recycle separately',
                    'Take to e-waste recycling centers',
                    'Consider manufacturer take-back programs',
                    'Erase personal data before disposal'
                ],
                'colors': ['#2B2D42', '#8D99AE', '#EDF2F4', '#EF233C', '#D90429'],
                'icon': '💻'
            },
            'Glass Waste': {
                'steps': [
                    'Rinse containers to remove residue',
                    'Sort by color (clear, green, brown)',
                    'Remove metal or plastic caps and lids',
                    'Take to glass recycling dropoff points'
                ],
                'colors': ['#CDDAFD', '#DFE7FD', '#F0EFEB', '#D7E3FC', '#CCDBFD'],
                'icon': '🥛'
            },
            'Hazardous Waste': {
                'steps': [
                    'Keep in original labeled containers',
                    'Never mix different hazardous materials',
                    'Store away from heat and children',
                    'Take to hazardous waste collection facilities'
                ],
                'colors': ['#FF9F1C', '#FFBF69', '#FFFFFF', '#CBF3F0', '#2EC4B6'],
                'icon': '⚠️'
            },
            'Metal Waste': {
                'steps': [
                    'Separate ferrous (magnetic) from non-ferrous metals',
                    'Clean off food residue',
                    'Flatten or crush containers to save space',
                    'Take to scrap yards or recycling centers'
                ],
                'colors': ['#5F0F40', '#9A031E', '#FB8B24', '#E36414', '#0F4C5C'],
                'icon': '🔧'
            },
            'Organic Waste': {
                'steps': [
                    'Separate from non-compostable items',
                    'Collect in compost bin with ventilation',
                    'Layer with brown materials (leaves, paper)',
                    'Use in garden or send to municipal composting'
                ],
                'colors': ['#606C38', '#283618', '#FEFAE0', '#DDA15E', '#BC6C25'],
                'icon': '🍎'
            },
            'Other': {
                'steps': [
                    'Check if material has recycling symbol',
                    'Research local guidelines for mixed materials',
                    'Contact waste authority for special disposal',
                    'Consider creative reuse options'
                ],
                'colors': ['#003049', '#D62828', '#F77F00', '#FCBF49', '#EAE2B7'],
                'icon': '❓'
            },
            'Paper Waste': {
                'steps': [
                    'Remove plastic wrapping, tape, and metal fasteners',
                    'Sort by type (cardboard, newspaper, mixed paper)',
                    'Keep dry and clean',
                    'Bundle or place in paper recycling bins'
                ],
                'colors': ['#EDEDE9', '#D6CCC2', '#F5EBE0', '#E3D5CA', '#D5BDAF'],
                'icon': '📄'
            },
            'Plastic Waste': {
                'steps': [
                    'Check recycling number (1-7) on bottom',
                    'Rinse containers to remove residue',
                    'Remove labels when possible',
                    'Compress to save space in recycling bin'
                ],
                'colors': ['#006466', '#065A60', '#0B525B', '#144552', '#1B3A4B'],
                'icon': '♳'
            },
            'Textile Waste': {
                'steps': [
                    'Donate clean, wearable items to charity',
                    'Repurpose damaged textiles as rags',
                    'Take to textile recycling collection points',
                    'Check with retailers for take-back programs'
                ],
                'colors': ['#F72585', '#7209B7', '#3A0CA3', '#4361EE', '#4CC9F0'],
                'icon': '👕'
            }
        }
        return guidance_data

    def get_guidance_for_waste_type(self, waste_type):
        """Get guidance information for a specific waste type"""
        if waste_type not in self.guidance_data:
            return None
            
        guidance = self.guidance_data[waste_type]
        
        # Add image paths
        guidance['main_image'] = f'/static/guidance/{waste_type.replace(" ", "_")}_main.png'
        guidance['step_images'] = [
            f'/static/guidance/{waste_type.replace(" ", "_")}_step{i+1}.png' 
            for i in range(len(guidance['steps']))
        ]
        
        return guidance
        
    def ensure_guidance_images(self):
        """Ensure that guidance images exist for all waste types"""
        for waste_type in self.waste_types:
            if waste_type in self.guidance_data:
                self._generate_guidance_images(waste_type)
    
    def _generate_guidance_images(self, waste_type):
        """Generate visual guidance images for a waste type"""
        # Skip if images already exist
        base_filename = os.path.join(self.guidance_folder, waste_type.replace(" ", "_"))
        main_image_path = f"{base_filename}_main.png"
        
        if os.path.exists(main_image_path):
            return
            
        guidance = self.guidance_data[waste_type]
        colors = guidance['colors']
        steps = guidance['steps']
        icon = guidance.get('icon', '♻️')
        
        # Generate main image
        img = self._create_main_guidance_image(waste_type, colors, icon)
        img.save(main_image_path)
        
        # Generate step images
        for i, step in enumerate(steps):
            step_img = self._create_step_guidance_image(
                step, 
                i+1, 
                len(steps), 
                colors[i % len(colors)], 
                waste_type
            )
            step_img.save(f"{base_filename}_step{i+1}.png")
    
    def _create_main_guidance_image(self, waste_type, colors, icon):
        """Create a main guidance image for a waste type"""
        width, height = 800, 400
        img = Image.new('RGB', (width, height), color=colors[0])
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Draw title
        title_text = f"{waste_type} {icon}"
        text_width = draw.textlength(title_text, font=title_font)
        draw.text(
            ((width - text_width) / 2, 80), 
            title_text, 
            fill=colors[2], 
            font=title_font
        )
        
        # Draw subtitle
        subtitle = "Proper Disposal Guide"
        subtitle_width = draw.textlength(subtitle, font=subtitle_font)
        draw.text(
            ((width - subtitle_width) / 2, 150), 
            subtitle, 
            fill=colors[2], 
            font=subtitle_font
        )
        
        # Draw decorative elements
        for i in range(5):
            offset = i * 60
            draw.rectangle(
                [offset, height - 100 + (i * 5), offset + 300, height - 50 + (i * 5)],
                fill=colors[i % len(colors)]
            )
        
        return img
    
    def _create_step_guidance_image(self, step_text, step_num, total_steps, color, waste_type):
        """Create an image for a specific disposal step"""
        width, height = 600, 300
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            header_font = ImageFont.truetype("arial.ttf", 24)
            step_font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            header_font = ImageFont.load_default()
            step_font = ImageFont.load_default()
        
        # Draw header
        header = f"{waste_type}: Step {step_num} of {total_steps}"
        draw.rectangle([0, 0, width, 50], fill=color)
        header_width = draw.textlength(header, font=header_font)
        draw.text(
            ((width - header_width) / 2, 10),
            header,
            fill='white',
            font=header_font
        )
        
        # Draw step text
        # Wrap text to fit width
        words = step_text.split()
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            test_line = current_line + " " + word
            if draw.textlength(test_line, font=step_font) < width - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        
        y_position = 80
        for line in lines:
            line_width = draw.textlength(line, font=step_font)
            draw.text(
                ((width - line_width) / 2, y_position),
                line,
                fill='black',
                font=step_font
            )
            y_position += 30
        
        # Draw progress bar
        progress_width = int((step_num / total_steps) * (width - 100))
        draw.rectangle([50, height - 50, width - 50, height - 30], outline='lightgray', width=1)
        draw.rectangle([50, height - 50, 50 + progress_width, height - 30], fill=color)
        
        return img

from flask import Blueprint, render_template

guidance_bp = Blueprint('guidance', __name__, template_folder='templates', static_folder='static')

waste_guidance = WasteGuidance(static_folder='static')

@guidance_bp.route('/guidance/<waste_type>')
def waste_guidance_view(waste_type):
    guidance = waste_guidance.get_guidance_for_waste_type(waste_type)
    if not guidance:
        return render_template('404.html'), 404
    # Remove dependency on WASTE_CATEGORIES since it's now internal
    waste_info = waste_guidance.guidance_data.get(waste_type, {})
    return render_template('waste_guidance.html', waste_type=waste_type, guidance=guidance, waste_info=waste_info)