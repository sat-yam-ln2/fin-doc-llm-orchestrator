SAMPLE_DOCS = {
    "bank_statement": """
Account Holder: John Meyers
Account Number: 4821-0093-2211
Statement Period: March 1 - March 31, 2024

Transactions:
03/02 - Withdrawal ATM - $500
03/07 - Transfer to Account 9900-1122 - $12,000
03/10 - Deposit Payroll - $3,200
03/15 - Wire Transfer International - $8,750 (flagged)
03/22 - POS Purchase - $45
03/28 - Withdrawal - $2,000

Total Credits: $3,200
Total Debits: $23,295
""",

    "invoice": """
Invoice #: INV-20240415
Vendor: Rapid Logistics Ltd
Buyer: Nexus Trading Co.
Invoice Date: April 15, 2024
Due Date: May 15, 2024

Line Items:
- Freight Services Q1: $14,000
- Handling Fee: $1,200
- Customs Clearance: $800

Total Amount Due: $16,000
Payment Terms: Wire Transfer Only
""",

    "dispute_letter": """
To Whom It May Concern,

I am writing to dispute a charge on my account number 7731-4492. On February 10, 2024, a transaction of $3,450 was posted that I did not authorize. I have no record of this purchase and have not received any goods or services for this amount.

I am requesting an immediate investigation and reversal of this charge.

Sincerely,
Angela Torres
""",

    "news_snippet": """
March 28, 2024 - Regulators have flagged Omega Capital Partners for potential money laundering activities. According to sources familiar with the matter, the firm processed over $40 million in suspicious cross-border transfers in Q1 2024. CEO David Lau has denied wrongdoing. The Financial Crimes Enforcement Network (FinCEN) has opened a formal investigation.
""",

    "ambiguous_memo": """
INTERNAL MEMO — COMPLIANCE REVIEW
Ref: CMP-2024-0391 | Date: April 2, 2024

This memo documents a formal complaint received from account holder Marcus Webb 
(Account No. 5593-8821) regarding a disputed transaction of $7,200 on March 29, 2024. 
The account holder states the charge was unauthorized.

Separately, our adverse media team flagged news reports linking the merchant — 
Trident Payment Solutions — to an ongoing FinCEN investigation into cross-border 
wire fraud and money laundering. CEO Raymond Holt denied the allegations.

Risk Operations recommends escalation given the overlap between the customer 
dispute and the regulatory investigation into the merchant.
"""
}
