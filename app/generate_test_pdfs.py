#!/usr/bin/env python3
"""
Generate sample PDFs for testing the form filler application.
Run this script to create questions.pdf and data.pdf
"""

from fpdf import FPDF
import os

def generate_questions_pdf(filename='questions.pdf'):
    """Generate a PDF with sample questions"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'Sample Questions Form', ln=True)
    pdf.ln(10)
    
    # Questions
    pdf.set_font('Helvetica', '', 12)
    questions = [
        "What is the applicant's full name?",
        "What is the applicant's date of birth?",
        "What is the applicant's current address?",
        "What is the applicant's email address?",
        "What is the applicant's phone number?",
        "What is the applicant's highest level of education?",
        "What is the applicant's current occupation?",
        "What are the applicant's work experience details?",
        "What programming languages does the applicant know?",
        "What is the applicant's expected salary?"
    ]
    
    for i, question in enumerate(questions, 1):
        pdf.cell(0, 10, f"{i}. {question}", ln=True)
        pdf.ln(5)
    
    pdf.output(filename)
    print(f"✓ Created {filename}")

def generate_data_pdf(filename='data.pdf'):
    """Generate a PDF with applicant data"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'Applicant Information', ln=True)
    pdf.ln(10)
    
    # Data
    pdf.set_font('Helvetica', '', 11)
    
    data_sections = [
        ("Personal Information:", [
            "Full Name: John Michael Smith",
            "Date of Birth: March 15, 1995",
            "Current Address: 1234 Silicon Valley Blvd, Apt 567,",
            "San Francisco, CA 94102",
            "Email Address: john.smith@email.com",
            "Phone Number: (555) 123-4567"
        ]),
        ("Education:", [
            "Highest Level of Education: Master of Science in",
            "Computer Science",
            "University: Stanford University",
            "Graduation Year: 2019",
            "GPA: 3.8/4.0"
        ]),
        ("Professional Information:", [
            "Current Occupation: Senior Software Engineer",
            "Company: Tech Innovations Inc.",
            "Years of Experience: 5 years"
        ]),
        ("Work Experience:", [
            "- Senior Software Engineer at Tech Innovations Inc.",
            "  (2021-Present)",
            "  Led development of microservices architecture",
            "  Managed team of 4 junior engineers",
            "  Implemented CI/CD pipelines",
            "",
            "- Software Engineer at StartUp Corp (2019-2021)",
            "  Developed full-stack web applications",
            "  Worked with React, Node.js, and PostgreSQL",
            "  Participated in agile development processes"
        ]),
        ("Technical Skills:", [
            "Programming Languages: Python, JavaScript,",
            "TypeScript, Java, Go",
            "Frameworks: React, Node.js, Django, Spring Boot",
            "Databases: PostgreSQL, MongoDB, Redis",
            "Cloud Platforms: AWS, Google Cloud Platform",
            "DevOps: Docker, Kubernetes, Jenkins, GitHub Actions"
        ]),
        ("Salary Information:", [
            "Expected Salary: $150,000 - $180,000 per year",
            "Current Salary: $140,000 per year"
        ])
    ]
    
    for section_title, lines in data_sections:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, section_title, ln=True)
        pdf.set_font('Helvetica', '', 11)
        
        for line in lines:
            if line:
                pdf.cell(0, 6, line, ln=True)
            else:
                pdf.ln(3)
        
        pdf.ln(5)
    
    pdf.output(filename)
    print(f"✓ Created {filename}")

def main():
    print("=" * 60)
    print("PDF Test Files Generator for Form Filler")
    print("=" * 60)
    print()
    
    # Check if fpdf2 is installed
    try:
        from fpdf import FPDF
    except ImportError:
        print("ERROR: fpdf2 is not installed!")
        print("Please run: pip install fpdf2")
        return
    
    # Generate PDFs
    print("Generating PDFs...")
    print()
    
    generate_questions_pdf()
    generate_data_pdf()
    
    print()
    print("=" * 60)
    print("✓ Success! PDFs created in current directory")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Check that questions.pdf and data.pdf are in this folder")
    print("2. Start your form filler app: uvicorn main:app --reload")
    print("3. Go to http://localhost:8000")
    print("4. Upload the two PDFs and click 'Fill Form'")
    print()

if __name__ == "__main__":
    main()
