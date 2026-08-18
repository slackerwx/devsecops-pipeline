using Xunit;

public class GreetingTests
{
    [Fact]
    public void GreetingIsStable() => Assert.Equal("fixture-dotnet", Program.Greeting());
}
