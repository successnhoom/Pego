import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const CreditTopUpModal = ({ isOpen, onClose }) => {
  const { topUpCredits, confirmPromptPayPayment, loading } = useAuth();
  const [step, setStep] = useState(1); // 1: amount, 2: payment method, 3: payment processing
  const [amount, setAmount] = useState(100);
  const [paymentMethod, setPaymentMethod] = useState('promptpay');
  const [paymentSession, setPaymentSession] = useState(null);

  // Predefined amounts
  const predefinedAmounts = [50, 100, 200, 500, 1000];

  if (!isOpen) return null;

  const handleAmountSubmit = () => {
    if (amount >= 10) {
      setStep(2);
    }
  };

  const handlePaymentMethodSubmit = async () => {
    setStep(3);
    
    const result = await topUpCredits(amount, paymentMethod);
    if (result.success) {
      setPaymentSession(result.data);
      
      if (paymentMethod === 'stripe' && result.data.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = result.data.checkout_url;
      }
    } else {
      setStep(2); // Go back to payment method selection
    }
  };

  const handlePromptPayConfirm = async () => {
    if (paymentSession?.session_id) {
      const result = await confirmPromptPayPayment(paymentSession.session_id);
      if (result.success) {
        onClose();
        resetModal();
      }
    }
  };

  const resetModal = () => {
    setStep(1);
    setAmount(100);
    setPaymentMethod('promptpay');
    setPaymentSession(null);
  };

  const handleClose = () => {
    onClose();
    resetModal();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6 relative max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl"
        >
          ×
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">💳 เติมเครดิต</h2>
          <p className="text-gray-600">เติมเครดิตสำหรับอัพโหลดวิดีโอ</p>
          <div className="text-sm text-blue-600 mt-2">
            1 บาท = 1 เครดิต | อัพโหลดวิดีโอ = 30 เครดิต
          </div>
        </div>

        {/* Step Indicator */}
        <div className="flex justify-center mb-6">
          <div className="flex items-center space-x-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              1
            </div>
            <div className={`w-8 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              2
            </div>
            <div className={`w-8 h-1 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              3
            </div>
          </div>
        </div>

        {/* Step 1: Amount Selection */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 text-center">
              เลือกจำนวนเงินที่ต้องการเติม
            </h3>
            
            {/* Predefined Amounts */}
            <div className="grid grid-cols-3 gap-3">
              {predefinedAmounts.map((preAmount) => (
                <button
                  key={preAmount}
                  onClick={() => setAmount(preAmount)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    amount === preAmount
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  <div className="text-lg font-bold">฿{preAmount}</div>
                  <div className="text-xs text-gray-500">{preAmount} เครดิต</div>
                </button>
              ))}
            </div>

            {/* Custom Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                หรือระบุจำนวนเอง (ขั้นต่ำ 10 บาท)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                min="10"
                max="10000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="ระบุจำนวนเงิน"
              />
            </div>

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">จำนวนเงิน:</span>
                <span className="font-bold text-lg">฿{amount}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">เครดิตที่ได้รับ:</span>
                <span className="font-bold text-lg text-blue-600">{amount} เครดิต</span>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                สามารถอัพโหลดวิดีโอได้ {Math.floor(amount / 30)} คลิป
              </div>
            </div>

            <button
              onClick={handleAmountSubmit}
              disabled={amount < 10}
              className={`w-full py-3 px-4 rounded-md font-medium transition-all ${
                amount < 10
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              ถัดไป - เลือกวิธีชำระเงิน
            </button>
          </div>
        )}

        {/* Step 2: Payment Method Selection */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 text-center">
              เลือกวิธีชำระเงิน
            </h3>

            <div className="space-y-3">
              {/* PromptPay */}
              <button
                onClick={() => setPaymentMethod('promptpay')}
                className={`w-full p-4 rounded-lg border-2 transition-all ${
                  paymentMethod === 'promptpay'
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-3xl">📱</div>
                  <div className="flex-1 text-left">
                    <h4 className="font-bold text-gray-900">PromptPay</h4>
                    <p className="text-sm text-gray-600">สแกน QR Code ด้วยแอปธนาคาร</p>
                  </div>
                  <div className="text-blue-600">
                    {paymentMethod === 'promptpay' && '✓'}
                  </div>
                </div>
              </button>

              {/* Stripe */}
              <button
                onClick={() => setPaymentMethod('stripe')}
                className={`w-full p-4 rounded-lg border-2 transition-all ${
                  paymentMethod === 'stripe'
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-3xl">💳</div>
                  <div className="flex-1 text-left">
                    <h4 className="font-bold text-gray-900">บัตรเครดิต/เดบิต</h4>
                    <p className="text-sm text-gray-600">Visa, MasterCard, JCB</p>
                  </div>
                  <div className="text-blue-600">
                    {paymentMethod === 'stripe' && '✓'}
                  </div>
                </div>
              </button>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">ยอดรวม:</span>
                <span className="font-bold text-lg">฿{amount}</span>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-3 px-4 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 transition-all"
              >
                ← กลับ
              </button>
              <button
                onClick={handlePaymentMethodSubmit}
                disabled={loading}
                className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
                  loading
                    ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {loading ? 'กำลังดำเนินการ...' : 'ชำระเงิน'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Payment Processing */}
        {step === 3 && paymentSession && (
          <div className="space-y-4">
            {paymentMethod === 'promptpay' && (
              <>
                <h3 className="text-lg font-semibold text-gray-900 text-center">
                  สแกน QR Code เพื่อชำระเงิน
                </h3>
                
                <div className="bg-white p-4 rounded-lg border text-center">
                  <img
                    src={paymentSession.qr_code}
                    alt="PromptPay QR Code"
                    className="mx-auto max-w-full h-64 object-contain"
                  />
                </div>

                <div className="text-center space-y-2">
                  <p className="text-gray-600">จำนวนเงิน: <span className="font-bold">฿{amount}</span></p>
                  <p className="text-sm text-gray-500">
                    สแกน QR Code ด้วยแอปธนาคารของคุณ
                  </p>
                  <p className="text-xs text-gray-400">
                    QR Code หมดอายุใน 10 นาที
                  </p>
                </div>

                <button
                  onClick={handlePromptPayConfirm}
                  disabled={loading}
                  className={`w-full py-3 px-4 rounded-md font-medium transition-all ${
                    loading
                      ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {loading ? 'กำลังยืนยัน...' : '✅ ยืนยันการชำระเงินแล้ว'}
                </button>

                <button
                  onClick={() => setStep(2)}
                  className="w-full py-2 px-4 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 transition-all"
                >
                  ← เปลี่ยนวิธีชำระเงิน
                </button>
              </>
            )}

            {paymentMethod === 'stripe' && (
              <div className="text-center space-y-4">
                <div className="text-6xl">🔄</div>
                <h3 className="text-lg font-semibold text-gray-900">
                  กำลังเปลี่ยนเส้นทาง...
                </h3>
                <p className="text-gray-600">
                  กำลังนำคุณไปยังหน้าชำระเงิน Stripe
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CreditTopUpModal;