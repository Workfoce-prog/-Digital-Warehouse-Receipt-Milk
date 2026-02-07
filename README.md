# Mali Dairy DWR Platform (Pilot) — Streamlit App

A full working prototype of a **Digital Warehouse Receipt (DWR/BDN)** system adapted to Mali’s milk industry:
- Women groups & cooperatives
- Independent women processors
- Small private dairies
- Licensed custodians (MCC/chillers/processors)
- Pilot-first: **in-house advances** + **tank rental / rent-to-own**
- Growth-stage: bank liens (scaffolded)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo logins
All demo accounts use password: `Admin123!`

- Platform admin: `platform_admin`
- Women group: `women_group`
- Woman processor: `woman_processor`
- Private dairy: `private_dairy`
- Custodian (MCC): `custodian_mcc`
- Government: `government`
- Buyer: `buyer_demo`
- Bank (demo): `bank_demo`

## Recommended demo flow
1) Tanks & Storage: assign a tank (rental/rent-to-own)
2) Intake & Tests (custodian): create a dairy lot
3) Issue DWR (platform/gov): issue receipt + PDF + QR payload
4) In-house Advance: create a pilot advance (sets receipt status to `advance_active`)
5) Sale & Settlement: create sale contract + confirm mobile money payment (auto-repays advance)
6) Release Orders: dispatch and close receipt
7) Cold Chain SLA + Audit Log

## Data
CSV storage lives in `/data/` for the pilot prototype. Replace with Postgres for production.
