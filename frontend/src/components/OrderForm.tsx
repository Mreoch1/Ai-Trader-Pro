import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface OrderFormProps {
  symbol: string;
  currentPrice: number;
  availableFunds: number;
  onOrderSubmit?: () => void;
}

const OrderForm: React.FC<OrderFormProps> = ({
  symbol,
  currentPrice,
  availableFunds,
  onOrderSubmit,
}) => {
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState<string>('');
  const [limitPrice, setLimitPrice] = useState<string>('');
  const queryClient = useQueryClient();

  const createOrderMutation = useMutation({
    mutationFn: async (order: any) => {
      const response = await fetch('/api/v1/trading/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create order');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      onOrderSubmit?.();
      // Reset form
      setQuantity('');
      setLimitPrice('');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const order = {
      symbol,
      side,
      type: orderType,
      quantity: Number(quantity),
      ...(orderType === 'limit' && { price: Number(limitPrice) }),
    };

    try {
      await createOrderMutation.mutateAsync(order);
    } catch (error) {
      console.error('Error creating order:', error);
    }
  };

  const estimatedCost = Number(quantity) * (orderType === 'limit' ? Number(limitPrice) : currentPrice);
  const isValidOrder = 
    Number(quantity) > 0 && 
    (orderType === 'market' || Number(limitPrice) > 0) &&
    (side === 'sell' || estimatedCost <= availableFunds);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {/* Order Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Order Type
          </label>
          <div className="mt-1">
            <select
              value={orderType}
              onChange={(e) => setOrderType(e.target.value as 'market' | 'limit')}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>
        </div>

        {/* Side Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Side
          </label>
          <div className="mt-1">
            <select
              value={side}
              onChange={(e) => setSide(e.target.value as 'buy' | 'sell')}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>
        </div>

        {/* Quantity Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Quantity
          </label>
          <div className="mt-1">
            <input
              type="number"
              min="0"
              step="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Limit Price Input */}
        {orderType === 'limit' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Limit Price
            </label>
            <div className="mt-1">
              <input
                type="number"
                min="0"
                step="0.01"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Order Summary */}
      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Order Summary
        </h4>
        <div className="space-y-1 text-sm">
          <p className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Symbol:</span>
            <span className="font-medium">{symbol}</span>
          </p>
          <p className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Current Price:</span>
            <span className="font-medium">${currentPrice.toFixed(2)}</span>
          </p>
          <p className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Estimated Cost:</span>
            <span className="font-medium">${estimatedCost.toFixed(2)}</span>
          </p>
          <p className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Available Funds:</span>
            <span className="font-medium">${availableFunds.toFixed(2)}</span>
          </p>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!isValidOrder || createOrderMutation.isPending}
        className={`w-full py-2 px-4 rounded-lg text-white font-medium
          ${isValidOrder
            ? 'bg-indigo-600 hover:bg-indigo-700'
            : 'bg-gray-400 cursor-not-allowed'
          }
        `}
      >
        {createOrderMutation.isPending ? 'Creating Order...' : 'Place Order'}
      </button>

      {/* Error Message */}
      {createOrderMutation.isError && (
        <div className="mt-2 text-sm text-red-600 dark:text-red-400">
          {createOrderMutation.error.message}
        </div>
      )}
    </form>
  );
};

export default OrderForm; 