"""Reproduce the research exhibits from dated filings and stated assumptions."""
import json
from decimal import Decimal as D, localcontext
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUTPUT = ROOT / "local" / "research-20261120" / "TSLA"
PRICE = D('345.82')
SHARES = D('3.952757946')
R = D('.10')
ROIC = D('.18')
RF = D('.0492')
K = D('-.005')
G = tuple(map(D, ('.015', '.025', '.035')))
PROBABILITY = tuple(map(D, ('.30', '.50', '.20')))
PROFITS_3Y = tuple(map(D, ('5', '12', '28')))
PROFITS_10Y = tuple(map(D, ('12', '55', '220')))
PE_3Y = tuple(map(D, ('20', '35', '60')))
RISKS = 'Cybercab认证及事故责任:情景,FSD与储能竞争:情景,SpaceX换股与关联方治理:未建模,重大地域断供:未建模'


def cmd(tool, *args):
    run = subprocess.run([sys.executable, str(ROOT / 'tools' / (tool + '.py')),
                          *map(str, args)], check=True, capture_output=True, text=True)
    return run.stdout


def reverse_dcf(cap, start, base_r, terminal_g):
    """Return implied compounding rate and its year-ten FCFE in billions."""
    def value(rate):
        pv = sum((start * (1 + rate) ** t / (1 + base_r) ** t
                  for t in range(1, 11)), D(0))
        terminal = start * (1 + rate) ** 10 * (1 + terminal_g) / (base_r - terminal_g)
        return pv + terminal / (1 + base_r) ** 10

    low, high = D(0), D(2)
    for _ in range(128):
        mid = (low + high) / 2
        if value(mid) < cap:
            low = mid
        else:
            high = mid
    return mid, start * (1 + mid) ** 10


def calc():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with localcontext() as ctx:
        ctx.prec = 40
        cap = PRICE * SHARES
        profit_ttm = D('2.378') + D('.840')
        earnings = profit_ttm / SHARES
        fcf = D('14.897') + D('3.813') - D('13.014') - D('2.393')
        sbc = D('3.346') + D('2.825') - D('1.871')
        lease_principal = D('.063') + D('.104') - D('.085')
        net_cash = D('45.447') - D('9.523')
        retail_plus_cash_eff = D('20.560') - D('.113')
        sales_q = D('28.046')
        inputs = {
            'r': R, 'roic': ROIC, 'rf': RF, 'k': K, 'g': G, 'probabilities': PROBABILITY,
            'market_cap_billions': cap, 'price': PRICE, 'shares_billions': SHARES,
            'ttm_revenue': D('78.669') + D('24.901'), 'ttm_profit': profit_ttm,
            'ttm_cfo': D('14.897') + D('3.813'), 'ttm_capex': D('13.014') + D('2.393'),
            'ttm_fcf': fcf, 'ttm_sbc': sbc, 'ttm_lease_principal': lease_principal,
            'ttm_fcf_after_sbc_principal': fcf - sbc - lease_principal,
            'ttm_operating_profit': D('2.057') + D('1.409'),
            'ttm_gross_profit': D('14.965') + D('5.009'),
            'net_cash_before_restricted': net_cash,
            'net_cash_after_restricted': net_cash - D('.231'),
            'net_cash_including_operating_lease': D('45.447')-D('.231')-D('16.445'),
            'estimated_ev': cap - net_cash + D('.231'),
            'ps': cap / D('103.570'), 'pe_published_eps': PRICE / D('.91'),
            'pe_legal_shares': cap / profit_ttm, 'pb': cap / D('89.289'),
            'ev_sales': (cap - net_cash + D('.231')) / D('103.570'),
            'fcf_yield': fcf / cap,
            'q3_auto_sales_share': D('20.560') / sales_q,
            'q3_energy_sales_share': D('2.881') / sales_q,
            'q3_service_sales_share': D('4.605') / sales_q,
            'q3_auto_gm': (D('20.560') - D('16.754')) / D('20.560'),
            'q3_auto_ex_credit_gm': (retail_plus_cash_eff - D('16.754')) / retail_plus_cash_eff,
            'q3_auto_ex_credit_tariff_gm': (retail_plus_cash_eff - D('16.754') - D('.260')) / retail_plus_cash_eff,
            'prior_auto_ex_credit_gm': (D('21.205')-D('.417')-D('17.590'))/(D('21.205')-D('.417')),
            'q3_energy_gm': (D('2.881') - D('1.927')) / D('2.881'),
            'prior_energy_gm': (D('3.415') - D('2.342')) / D('3.415'),
            'q3_energy_ex_tariff_gm': (D('2.881')+D('.339')-D('1.927')-D('.526')) / (D('2.881')+D('.339')),
            'q3_energy_revenue_ex_tariff': D('2.881') + D('.339'),
            'q3_tariff_net': D('.526') + D('.260') - D('.339'),
            'q3_operating_ex_tariffs': D('.718') - D('.526') - D('.260') + D('.339'),
            'q3_operating_ex_tariffs_credit': D('.718') - D('.526') - D('.260') + D('.339') - D('.113'),
            'q3_service_gm': (D('4.605') - D('3.871')) / D('4.605'),
            'q3_delivery_growth': D(486532)/D(497099)-1,
            'q3_storage_growth': D('13.7')/D('12.5')-1,
            'q3_group_margin': (sales_q-D('22.552'))/sales_q,
            'q3_group_operating_margin': D('.718')/sales_q,
            'q3_rnd_growth': D('2.761')/D('1.630')-1,
            'q3_net_profit_growth': D('.787')/D('1.373')-1,
            'award_fraction': D('.423743904')/SHARES,
            'three_year_profit_at_current_price_pe60': PRICE*SHARES*(1+R)**3/D('60'),
            'reverse_dcf': reverse_dcf(cap, fcf, R, G[1]),
            'reverse_dcf_if_excess_net_cash': reverse_dcf(cap-(net_cash-D('.231')), fcf, R, G[1]),
        }
        threes = []
        tens = []
        earnings_multiple = D(1) / D(3)
        for gp, p, p3, p10, pe3 in zip(G, PROBABILITY, PROFITS_3Y, PROFITS_10Y, PE_3Y):
            target = p3 * pe3 / SHARES
            threes.append({'profit': p3, 'pe': pe3, 'eps': p3 / SHARES,
                           'cagr': (p3/profit_ttm)**earnings_multiple - 1,
                           'target': target, 'present_value': target / (1 + R) ** 3,
                           'annualized_return': (target/PRICE)**earnings_multiple-1})
            terminal_pe = (1 - gp / ROIC) / (R-gp)
            irr = (p10 * terminal_pe / cap) ** (D(1)/10) - 1 + K
            tens.append({'p': p, 'profit': p10, 'g': gp, 'spread': R-gp, 'pe':terminal_pe, 'irr':irr,
                         'required_profit': cap * (1 + R - K) ** 10 / terminal_pe})
        inputs['three_year'] = threes
        inputs['ten_year'] = tens
        inputs['weighted_irr'] = sum(t['p']*t['irr'] for t in tens)
        inputs['payout_irr_base_percents'] = [100*t['irr'] for t in tens]
        inputs['expected_pv3'] = sum(row['present_value']*p for row,p in zip(threes,PROBABILITY))
        inputs['three_year_without_award_base'] = PROFITS_3Y[1]*PE_3Y[1]/(SHARES-D('.423743904'))/(1+R)**3
        logs = [
            cmd('financial_rigor', 'verify-market-cap', '--price', PRICE, '--shares', SHARES*10**9,
                '--reported', D('1.37e12'), '--currency', 'USD'),
            cmd('financial_rigor', 'verify-valuation', '--price', PRICE, '--eps', '.91',
                '--bvps', D('89.289')/SHARES, '--fcf-per-share', fcf/SHARES,
                '--revenue-per-share', D('103.570')/SHARES),
        ]
        comparisons = {
            '普通收盘': {'StockAnalysis':345.82,'MarketScreener':345.82,'Google Finance':345.82},
            '普通股数（百万股）': {'SEC 10-Q':3952.757946,'Google Finance':3950},
            'FY2025收入': {'SEC 10-K':94.827,'StockAnalysis':94.827,'MacroTrends':94.827},
            'FY2025归母': {'SEC 10-K':3.794,'StockAnalysis':3.794,'MacroTrends':3.794},
            'Q3 2026收入': {'SEC 10-Q':28.046,'StockAnalysis':28.046,'Reuters-LSEG':28.05},
            'Q3 2026归母': {'SEC 10-Q':.787,'StockAnalysis':.787,'Associated Press':.787},
            'Q3 2026现金及短投': {'SEC 10-Q':45.447,'StockAnalysis':45.447},
            'TTM归母': {'SEC 10-K/10-Q':3.218,'StockAnalysis':3.220,'Trefis':3.218},
            '扣保险受限并计入经营租赁净现金': {'SEC加减计算':28.771,'Trefis':28.771},
        }
        for field, sources in comparisons.items():
            logs.append(cmd('financial_rigor','cross-validate','--field',field,
                            '--values',json.dumps(sources,ensure_ascii=False),'--tolerance','1'))
        logs.append(cmd('financial_rigor','three-scenario','--price',PRICE,'--eps',earnings,
                        '--shares',SHARES*10,'--growth',*[x['cagr'] for x in threes[::-1]],
                        '--pe',*PE_3Y[::-1],'--years','3','--currency','USD'))
        logs.append(cmd('terminal_value', 'audit', '--currency','USD','--r',R,'--roic',ROIC,
                        '--g',','.join(map(str,G)),'--rf',RF,'--beta','1.0','--discrete-risks',RISKS))
        for x in tens:
            logs.append(cmd('terminal_value','pe','--roic',ROIC,'--g',x['g'],'--r',R))
            logs.append(cmd('terminal_value','irr','--profit',x['profit'],'--mcap',cap,
                            '--pe',x['pe'],'--years','10','--payout',K))
        config = {'TSLA': {'roic': float(ROIC), 'g': [float(g) for g in G],
                           'p': [float(p) for p in PROBABILITY], 'irr10': [float(y) for y in inputs['payout_irr_base_percents']],
                           'k':float(K)}}
        (OUTPUT/'terminal-config.json').write_text(json.dumps(config,indent=2)+'\n')
        for delta in ('.02','.01'):
            logs.append(cmd('terminal_value','flip','--config',OUTPUT/'terminal-config.json','--name','TSLA',
                            '--r',R,'--delta',delta,'--currency','USD','--rf',RF))
        (OUTPUT/'model-results.json').write_text(json.dumps(inputs,indent=2,default=str)+'\n')
        (OUTPUT/'validation-log.txt').write_text('\n'.join(logs))


if __name__ == '__main__':
    calc()
