// Power Query M script for loading Online Retail II Star Schema CSVs
let
    SourceDir = "D:\github\go to offer\data-analyst\retail-customer-analytics\powerbi\",
    LoadFact = Csv.Document(File.Contents(SourceDir & "fact_transactions.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedFact = Table.PromoteHeaders(LoadFact, [PromoteAllScalars=true]),
    TypedFact = Table.TransformColumnTypes(PromotedFact, {
        {"transaction_id", Int64.Type},
        {"invoice_no", type text},
        {"invoice_day", type date},
        {"customer_id", Int64.Type},
        {"stock_code", type text},
        {"country", type text},
        {"quantity", Int64.Type},
        {"unit_price", type number},
        {"line_amount", type number},
        {"is_cancelled", type logical}
    })
in
    TypedFact
