import { X, Database, Layers, KeyRound, Link2 } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  schemaMarkdown: string;
}

export const SchemaModal = ({ isOpen, onClose, schemaMarkdown }: Props) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden border border-slate-200 animate-in zoom-in-95 duration-200 flex flex-col max-h-[88vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/80">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <Database size={16} />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Enterprise PostgreSQL Schema Inspector</h3>
              <p className="text-[11px] text-slate-500 font-mono">public schema • 6 interconnected tables • 60+ dimensional attributes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Subheader info */}
        <div className="px-6 py-3 bg-blue-50/50 border-b border-blue-100/60 flex items-center justify-between text-xs text-blue-900">
          <div className="flex items-center space-x-2">
            <Layers size={14} className="text-blue-600 shrink-0" />
            <span className="text-[11px]">
              Multi-table schema introspected at runtime with profit margins, marketing attribution, carrier SLAs, and inventory health.
            </span>
          </div>
          <span className="text-[10px] font-mono font-semibold bg-blue-100/80 text-blue-700 px-2 py-0.5 rounded-md shrink-0">
            6 Tables Active
          </span>
        </div>

        {/* Modal Content Grid */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {/* 1. Customers Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-blue-600" />
                  <span>customers</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  18 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-blue-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span>customer_code</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>full_name</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>email</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>gender</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>age_group</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>city</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>state</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>region</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-indigo-600 font-medium">customer_segment</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-medium">acquisition_channel</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>lifetime_value_tier</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>signup_date</span><span className="text-slate-400">DATE</span></li>
              </ul>
            </div>

            {/* 2. Sellers Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-teal-600" />
                  <span>sellers</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  8 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-teal-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span>seller_code</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>seller_name</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>city</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>state</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>rating</span><span className="text-slate-400">NUMERIC(3,2)</span></li>
                <li className="pt-1 flex items-center justify-between"><span>commission_rate</span><span className="text-slate-400">NUMERIC(4,3)</span></li>
                <li className="pt-1 flex items-center justify-between"><span>fulfillment_type</span><span className="text-slate-400">VARCHAR</span></li>
              </ul>
            </div>

            {/* 3. Products Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-emerald-600" />
                  <span>products</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  15 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span>sku</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>product_name</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-blue-600 font-medium">brand</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-medium">primary_category</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>sub_category</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>cost_price</span><span className="text-slate-400">NUMERIC(10,2)</span></li>
                <li className="pt-1 flex items-center justify-between"><span>selling_price</span><span className="text-slate-400">NUMERIC(10,2)</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-amber-600 font-medium">margin_amount</span><span className="text-slate-400">NUMERIC(10,2)</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-rose-600 font-medium">stock_quantity</span><span className="text-slate-400">INT</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-rose-600 font-medium">reorder_level</span><span className="text-slate-400">INT</span></li>
                <li className="pt-1 flex items-center justify-between"><span>rating</span><span className="text-slate-400">NUMERIC(3,2)</span></li>
              </ul>
            </div>

            {/* 4. Orders Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-amber-600" />
                  <span>orders</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  18 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-amber-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-blue-600 font-medium flex items-center space-x-1"><Link2 size={10} /><span>customer_id</span></span><span className="text-slate-400">INT FK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-teal-600 font-medium flex items-center space-x-1"><Link2 size={10} /><span>seller_id</span></span><span className="text-slate-400">INT FK</span></li>
                <li className="pt-1 flex items-center justify-between"><span>order_date</span><span className="text-slate-400">DATE</span></li>
                <li className="pt-1 flex items-center justify-between"><span>status</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>payment_method</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>subtotal_amount</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>discount_amount</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>tax_amount</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-medium">total_amount</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>coupon_code</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>delivery_days</span><span className="text-slate-400">INT</span></li>
              </ul>
            </div>

            {/* 5. Order Items Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-violet-600" />
                  <span>order_items</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  9 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-violet-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-amber-600 font-medium flex items-center space-x-1"><Link2 size={10} /><span>order_id</span></span><span className="text-slate-400">INT FK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-medium flex items-center space-x-1"><Link2 size={10} /><span>product_id</span></span><span className="text-slate-400">INT FK</span></li>
                <li className="pt-1 flex items-center justify-between"><span>quantity</span><span className="text-slate-400">INT</span></li>
                <li className="pt-1 flex items-center justify-between"><span>unit_cost_price</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>unit_selling_price</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>total_item_revenue</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-emerald-600 font-semibold">item_profit_margin</span><span className="text-slate-400">NUMERIC</span></li>
                <li className="pt-1 flex items-center justify-between"><span>return_status</span><span className="text-slate-400">VARCHAR</span></li>
              </ul>
            </div>

            {/* 6. Shipments Table */}
            <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                  <Database size={13} className="text-indigo-600" />
                  <span>shipments</span>
                </span>
                <span className="text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded-md text-slate-500">
                  7 cols
                </span>
              </div>
              <ul className="text-[11px] font-mono text-slate-600 space-y-1 divide-y divide-slate-100 max-h-48 overflow-y-auto pr-1">
                <li className="pt-1 flex items-center justify-between"><span className="text-indigo-600 font-medium flex items-center space-x-1"><KeyRound size={10} /><span>id</span></span><span className="text-slate-400">SERIAL PK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-amber-600 font-medium flex items-center space-x-1"><Link2 size={10} /><span>order_id</span></span><span className="text-slate-400">INT FK</span></li>
                <li className="pt-1 flex items-center justify-between"><span className="text-indigo-600 font-medium">carrier</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>tracking_number</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>status</span><span className="text-slate-400">VARCHAR</span></li>
                <li className="pt-1 flex items-center justify-between"><span>dispatch_date</span><span className="text-slate-400">DATE</span></li>
                <li className="pt-1 flex items-center justify-between"><span>delivery_date</span><span className="text-slate-400">DATE</span></li>
              </ul>
            </div>
          </div>

          {/* Raw Markdown Accordion/Block */}
          <div className="pt-2">
            <details className="group rounded-xl border border-slate-200 bg-white">
              <summary className="cursor-pointer px-4 py-2.5 text-xs font-mono font-medium text-slate-600 flex items-center justify-between">
                <span>View Full Markdown Schema Prompt</span>
                <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="p-4 bg-slate-900 text-slate-100 rounded-b-xl font-mono text-[11px] leading-relaxed whitespace-pre-wrap overflow-x-auto">
                {schemaMarkdown}
              </div>
            </details>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-2xs transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
