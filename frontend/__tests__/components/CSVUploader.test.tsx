import { render, screen } from '@testing-library/react';
import CSVUploader from '@/components/CSVUploader';

describe('CSVUploader', () => {
  it('renders upload interface', () => {
    render(<CSVUploader />);
    expect(screen.getByText(/Upload Network Traffic Data/i)).toBeInTheDocument();
    expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
  });

  it('displays file input', () => {
    render(<CSVUploader />);
    const input = document.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('accept', '.csv');
  });
});
